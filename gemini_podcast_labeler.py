import os
import sys
import json
import csv
import time
import signal
import asyncio
import aiosqlite
from multiprocessing import freeze_support
from dotenv import load_dotenv
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY_NIK")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")
# Rate limiting variables with default values
LLM_RATE_LIMIT = int(os.getenv("LLM_RATE_LIMIT", 1500))  # Default: 5 requests
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", 60))  # Default: 70 seconds
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", 10))  # Default: 10 concurrent requests

# Track API calls for rate limiting - initialize as regular lists
api_call_timestamps = []
failed_podcasts = []

# Create a semaphore to control API request rate and a lock for shared resources
api_semaphore = None  # Will be initialized in async context
timestamps_lock = None  # Will be initialized in async context

def write_failed_podcasts():
    """Write the list of failed podcasts to a file"""
    if failed_podcasts:
        print(f"Writing {len(failed_podcasts)} failed podcasts to failed_podcasts.txt")
        with open("failed_podcasts.txt", "w", encoding="utf-8") as f:
            for podcast in failed_podcasts:
                f.write(f"{podcast}\n")
    else:
        print("No failed podcasts to write")

def signal_handler(sig, frame):
    """Handle Ctrl+C by writing failed podcasts and exiting"""
    print("\nInterrupted! Writing failed podcasts before exiting...")
    write_failed_podcasts()
    sys.exit(0)

# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

async def check_rate_limit():
    """Enforce rate limiting for API calls with async support"""
    global api_call_timestamps
    current_time = time.time()
    
    # Use semaphore to control concurrent access to shared resource
    async with timestamps_lock:
        # Remove timestamps older than the rate limit period
        api_call_timestamps = [t for t in api_call_timestamps if current_time - t < RATE_LIMIT_PERIOD]
        
        # If we've reached the limit, wait until we can make another call
        if len(api_call_timestamps) >= LLM_RATE_LIMIT:
            oldest_timestamp = min(api_call_timestamps) if api_call_timestamps else current_time
            sleep_time = RATE_LIMIT_PERIOD - (current_time - oldest_timestamp)
            if sleep_time > 0:
                print(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                await asyncio.sleep(sleep_time)
                # After waiting, clear expired timestamps and start fresh
                api_call_timestamps = []
        
        # Record this API call
        api_call_timestamps.append(current_time)

async def score_podcast(podcast_name) -> str:
    # Apply rate limiting
    await check_rate_limit()
    
    client = genai.Client(api_key=API_KEY)
    model_id = LLM_MODEL

    # read prompt from prompt.txt
    with open("prompt.txt", "r") as f:
        prompt = f.read()
    prompt = "You are researching this podcast:" + podcast_name + "\n" + prompt

    google_search_tool = Tool(
        google_search = GoogleSearch()
    )

    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        )
    )
    out = ""
    for each in response.candidates[0].content.parts:
        out += each.text
    first_kept_idx = out.find('{')
    last_kept_idx = out.rfind('}')
    if first_kept_idx == -1:
        first_kept_idx = 0
    if last_kept_idx == -1:
        last_kept_idx = len(out) - 1
    out = out[first_kept_idx:last_kept_idx+1]
    return out

async def get_podcast_scores(podcast_name: str) -> dict:
    try:
        out = await score_podcast(podcast_name)
        try:
            out_dict = json.loads(out)
            # Verify that the returned data is complete
            if not out_dict or not isinstance(out_dict, dict):
                print(f"Invalid data structure for '{podcast_name}': not a dictionary")
                async with timestamps_lock:
                    failed_podcasts.append(podcast_name)
                return {}
            return out_dict
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for '{podcast_name}': {e}")
            async with timestamps_lock:
                failed_podcasts.append(podcast_name)
            return {}
    except Exception as e:
        print(f"Error processing podcast '{podcast_name}': {str(e)}")
        async with timestamps_lock:
            failed_podcasts.append(podcast_name)
        return {}

async def process_podcast(podcast_name, genre, features, db_path, existing_podcasts):
    # Only skip podcasts that already exist in the database AND have complete data
    if podcast_name in existing_podcasts and existing_podcasts[podcast_name]['complete']:
        print(f"Skipping existing podcast with complete data: {podcast_name}")
        return
    elif podcast_name in existing_podcasts:
        print(f"Reprocessing existing podcast with incomplete data: {podcast_name}")
        
    print(f"Processing podcast: {podcast_name}")
    scores = await get_podcast_scores(podcast_name)
    
    # Skip if we couldn't get scores
    if not scores:
        print(f"Skipping database insertion for '{podcast_name}' due to missing or invalid data")
        return
    
    # Check if all required values exist and are valid
    valid_data = True
    values = [podcast_name, genre]
    for feature in features:
        value = scores.get(feature)
        try:
            # Convert to float and check if it's a valid number
            if value is not None:
                float_value = float(value)
                # Check if it's a reasonable value (not inf, nan, etc.)
                if not (isinstance(float_value, (int, float)) and -100 <= float_value <= 100):
                    print(f"Invalid value for '{feature}' in podcast '{podcast_name}': {value}")
                    valid_data = False
                    break
                values.append(float_value)
            else:
                # None values are not allowed
                print(f"Missing value for '{feature}' in podcast '{podcast_name}'")
                valid_data = False
                break
        except (ValueError, TypeError):
            print(f"Cannot convert value for '{feature}' to float in podcast '{podcast_name}': {value}")
            valid_data = False
            break
    
    # Only insert if all data is valid
    if not valid_data:
        print(f"Skipping database insertion for '{podcast_name}' due to invalid data")
        async with timestamps_lock:
            failed_podcasts.append(podcast_name)
        return
        
    # Insert into database
    async with aiosqlite.connect(db_path) as db:
        # Prepare and execute the database insertion
        columns = ["podcast_name", "genre"] + features
        placeholders = ",".join(["?"] * len(columns))
        insert_query = f"INSERT INTO podcasts ({', '.join([f'\"{col}\"' for col in columns])}) VALUES ({placeholders})"
        await db.execute(insert_query, values)
        await db.commit()
        print(f"Inserted scores for podcast: {podcast_name}")

async def process_all_podcasts():
    # List of features as defined in the prompt
    features = [
        "Comedic",
        "Controversy",
        "Consistency",
        "Thought Provoking",
        "Bias",
        "Expressivness",
        "Exciting",
        "Pacing",
        "Level of fiction",
        "Narrative",
        "Originality",
        "Production Quality",
        "Positivity",
        "Personal",
        "Educational",
        "Conservative",
        "Progressive",
        "Equity - minded",
        "Adult Content",
        "Explicit Language",
        "Self Improvement",
        "Family oriented",
        "Historical Focus",
        "Modern Focus"
    ]
    
    # Initialize locks for concurrency control
    global api_semaphore, timestamps_lock
    api_semaphore = asyncio.Semaphore(LLM_RATE_LIMIT)
    timestamps_lock = asyncio.Lock()
    
    db_path = "podcasts.db"
    
    # Initialize the database
    async with aiosqlite.connect(db_path) as db:
        # Create the podcasts table if it does not exist
        create_stmt = """CREATE TABLE IF NOT EXISTS podcasts (
          podcast_name TEXT,
          genre TEXT,"""
        for feature in features:
            create_stmt += f'"{feature}" REAL,'
        create_stmt = create_stmt.rstrip(',') + ")"
        await db.execute(create_stmt)
        await db.commit()
        
        # Get list of podcasts already in the database and check for NULL values in features
        query = "SELECT podcast_name, " + ", ".join([f'"{feature}"' for feature in features]) + " FROM podcasts"
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        
        # Create a dictionary of existing podcasts with a flag indicating if they have complete data
        existing_podcasts = {}
        for row in rows:
            podcast_name = row[0]
            # Check if any of the feature columns have NULL values
            feature_values = row[1:]
            has_null = any(val is None for val in feature_values)
            existing_podcasts[podcast_name] = {'complete': not has_null}
        
        print(f"Found {len(existing_podcasts)} podcasts already in database")
        incomplete_count = sum(1 for info in existing_podcasts.values() if not info['complete'])
        print(f"Of these, {incomplete_count} podcasts have incomplete data and will be reprocessed")
    
    try:
        # Open and read the CSV file
        tasks = []
        with open("combined_podcast_list.csv", newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                podcast_name = row.get("Name")
                genre = row.get("Genre")
                if not podcast_name:
                    continue
                
                # Create task for processing this podcast
                task = process_podcast(podcast_name, genre, features, db_path, existing_podcasts)
                tasks.append(task)
        
        # Process podcasts concurrently with limits
        for batch in [tasks[i:i+CONCURRENT_REQUESTS] for i in range(0, len(tasks), CONCURRENT_REQUESTS)]:
            await asyncio.gather(*batch)
            
        # Write any failed podcasts to file at the end
        write_failed_podcasts()
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        write_failed_podcasts()
    
    print("All podcasts have been processed and inserted into podcasts.db.")

async def process_single_podcast(podcast_name):
    global api_semaphore, timestamps_lock
    api_semaphore = asyncio.Semaphore(1)
    timestamps_lock = asyncio.Lock()
    podcast_scores = await get_podcast_scores(podcast_name)
    print("Podcast Scores:", podcast_scores)

if __name__ == "__main__":
    # Add freeze_support for multiprocessing
    freeze_support()
    
    try:
        # Run the CSV processing if the argument is 'csv'
        if len(sys.argv) == 2:
            if sys.argv[1].lower() == "csv":
                asyncio.run(process_all_podcasts())
            else:
                podcast_name = sys.argv[1]
                if not podcast_name:
                    print("Podcast name cannot be empty.")
                    sys.exit(1)
                asyncio.run(process_single_podcast(podcast_name))
        else:
            print("Usage:")
            print("  To process a single podcast: python gemini_podcast_labeler.py <podcast_name>")
            print("  To process all podcasts in Data_set.csv: python gemini_podcast_labeler.py csv")
            sys.exit(1)
    finally:
        # Write failed podcasts when the script exits
        if failed_podcasts:
            write_failed_podcasts()
