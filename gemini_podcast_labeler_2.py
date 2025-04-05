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

API_KEY = os.getenv("GOOGLE_API_KEY_ROM")
LLM_MODEL = os.getenv("LLM_MODEL_2", "gemini-2.0-flash-exp")
# Rate limiting variables with default values
LLM_RATE_LIMIT = int(os.getenv("LLM_RATE_LIMIT_2", 2000))  # Default: 5 requests
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD_2", 60))  # Default: 70 seconds
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS_2", 100))  # Default: 10 concurrent requests

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

    # read prompt from prompt_2.txt
    with open("prompt_2.txt", "r") as f:
        prompt = f.read()
    prompt = "You are researching this podcast:" + podcast_name + "\n" + prompt

    google_search_tool = Tool(
        google_search = GoogleSearch()
    )

    try:
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
        
        # Debug: Print raw response
        print(f"Raw LLM response for {podcast_name}: {out[:200]}...")
        
        first_kept_idx = out.find('{')
        last_kept_idx = out.rfind('}')
        if first_kept_idx == -1:
            print(f"Warning: No opening brace found in response for {podcast_name}")
            first_kept_idx = 0
        if last_kept_idx == -1:
            print(f"Warning: No closing brace found in response for {podcast_name}")
            last_kept_idx = len(out) - 1
        out = out[first_kept_idx:last_kept_idx+1]
        
        # Debug: Print JSON extract
        print(f"Extracted JSON for {podcast_name}: {out[:200]}...")
        
        return out
    except Exception as e:
        print(f"Error in score_podcast for '{podcast_name}': {str(e)}")
        raise

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
                
            # Fix capitalization issues with tag names by normalizing them
            normalized_dict = {}
            tags = [
                "Finance", "Romance", "Self-Improvment", "Interviews", "Video Games", 
                "Comedy", "True Crime", "Technology", "Politics", "History", 
                "Sports", "Health and Wellness", "Education", "Business", "Storytelling", 
                "Art and Design", "Literature", "Food and Drink", "Travel", "Environment", 
                "Spirituality", "Parenting", "Relationships", "Lifestyle", "Entrepreneurship", 
                "Documentary"
            ]
            
            # Map the response keys to our expected keys (case-insensitive)
            for tag in tags:
                # Try exact match first
                if tag in out_dict:
                    normalized_dict[tag] = out_dict[tag]
                else:
                    # Try case-insensitive match
                    for key in out_dict:
                        if key.lower() == tag.lower():
                            normalized_dict[tag] = out_dict[key]
                            break
            
            return normalized_dict
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for '{podcast_name}': {e}")
            print(f"JSON content was: {out}")
            async with timestamps_lock:
                failed_podcasts.append(podcast_name)
            return {}
    except Exception as e:
        print(f"Error processing podcast '{podcast_name}': {str(e)}")
        async with timestamps_lock:
            failed_podcasts.append(podcast_name)
        return {}

async def process_podcast(podcast_name, genre, tags, db_path, podcast_tag_status):
    # Only skip if this podcast already has values for all the tags
    if podcast_name in podcast_tag_status and all(podcast_tag_status[podcast_name].values()):
        print(f"Skipping podcast with complete tags: {podcast_name}")
        return
        
    print(f"Processing podcast: {podcast_name}")
    scores = await get_podcast_scores(podcast_name)
    
    # Skip if we couldn't get scores
    if not scores:
        print(f"Skipping database insertion for '{podcast_name}' due to missing or invalid data")
        return
    
    # Debug: Print the actual scores received
    print(f"Received scores for {podcast_name}: {scores}")
    
    # Check if all required values exist and are valid
    valid_data = True
    values = []
    
    # Prepare for UPDATE or INSERT based on whether the podcast exists
    if podcast_name in podcast_tag_status:
        # Update existing podcast with new tag values
        column_updates = []
        for tag in tags:
            value = scores.get(tag)
            try:
                # Convert to int and check if it's a valid binary value (0 or 1)
                if value is not None:
                    int_value = int(value)
                    if int_value not in [0, 1]:
                        print(f"Invalid binary value for '{tag}' in podcast '{podcast_name}': {value}")
                        valid_data = False
                        break
                    values.append(int_value)
                    column_updates.append(f'"{tag}" = ?')
                else:
                    # None values are not allowed
                    print(f"Missing value for '{tag}' in podcast '{podcast_name}'")
                    valid_data = False
                    break
            except (ValueError, TypeError):
                print(f"Cannot convert value for '{tag}' to int in podcast '{podcast_name}': {value}")
                valid_data = False
                break
        
        # Only update if all data is valid
        if not valid_data:
            print(f"Skipping database update for '{podcast_name}' due to invalid data")
            async with timestamps_lock:
                failed_podcasts.append(podcast_name)
            return
            
        # Update database
        async with aiosqlite.connect(db_path) as db:
            values.append(podcast_name)  # For the WHERE clause
            update_query = f"UPDATE podcasts SET {', '.join(column_updates)} WHERE podcast_name = ?"
            # Debug: Print the actual SQL query and values
            print(f"Executing SQL: {update_query} with values {values}")
            await db.execute(update_query, values)
            await db.commit()
            print(f"Updated tags for podcast: {podcast_name}")
    else:
        # Insert new podcast with tag values
        values = [podcast_name, genre]
        for tag in tags:
            value = scores.get(tag)
            try:
                # Convert to int and check if it's a valid binary value
                if value is not None:
                    int_value = int(value)
                    if int_value not in [0, 1]:
                        print(f"Invalid binary value for '{tag}' in podcast '{podcast_name}': {value}")
                        valid_data = False
                        break
                    values.append(int_value)
                else:
                    # None values are not allowed
                    print(f"Missing value for '{tag}' in podcast '{podcast_name}'")
                    valid_data = False
                    break
            except (ValueError, TypeError):
                print(f"Cannot convert value for '{tag}' to int in podcast '{podcast_name}': {value}")
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
            columns = ["podcast_name", "genre"] + tags
            placeholders = ",".join(["?"] * len(columns))
            insert_query = f"INSERT INTO podcasts ({', '.join([f'\"{col}\"' for col in columns])}) VALUES ({placeholders})"
            # Debug: Print the actual SQL query and values
            print(f"Executing SQL: {insert_query} with values {values}")
            await db.execute(insert_query, values)
            await db.commit()
            print(f"Inserted tags for podcast: {podcast_name}")

async def process_all_podcasts():
    # List of tags as defined in prompt_2.txt
    tags = [
        "Finance",
        "Romance",
        "Self-Improvment",
        "Interviews",
        "Video Games",
        "Comedy",
        "True Crime",
        "Technology",
        "Politics",
        "History",
        "Sports",
        "Health and Wellness",
        "Education",
        "Business",
        "Storytelling",
        "Art and Design",
        "Literature",
        "Food and Drink",
        "Travel",
        "Environment",
        "Spirituality",
        "Parenting",
        "Relationships",
        "Lifestyle",
        "Entrepreneurship",
        "Documentary"
    ]
    
    # Initialize locks for concurrency control
    global api_semaphore, timestamps_lock
    api_semaphore = asyncio.Semaphore(LLM_RATE_LIMIT)
    timestamps_lock = asyncio.Lock()
    
    db_path = "podcasts.db"
    
    # Initialize the database and check existing podcasts
    async with aiosqlite.connect(db_path) as db:
        # First, check if the table exists
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='podcasts'")
        table_exists = await cursor.fetchone()
        
        if not table_exists:
            # Create the podcasts table if it does not exist
            create_stmt = """CREATE TABLE IF NOT EXISTS podcasts (
              podcast_name TEXT PRIMARY KEY,
              genre TEXT,"""
            for tag in tags:
                create_stmt += f'"{tag}" INTEGER,'
            create_stmt = create_stmt.rstrip(',') + ")"
            await db.execute(create_stmt)
            await db.commit()
            print("Created new podcasts table")
        else:
            # Check if we need to add any new columns for our tags
            cursor = await db.execute("PRAGMA table_info(podcasts)")
            columns = await cursor.fetchall()
            existing_columns = {column[1] for column in columns}
            
            # Add any missing tag columns
            for tag in tags:
                if tag not in existing_columns:
                    await db.execute(f'ALTER TABLE podcasts ADD COLUMN "{tag}" INTEGER')
                    print(f"Added new column: {tag}")
            await db.commit()
        
        # Get list of podcasts and their tag status (NULL or not)
        podcast_tag_status = {}
        try:
            query = f"SELECT podcast_name, {', '.join([f'\"{tag}\"' for tag in tags])} FROM podcasts"
            print(f"Executing query: {query}")
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            
            for row in rows:
                podcast_name = row[0]
                tag_values = {tag: row[i+1] is not None for i, tag in enumerate(tags)}
                podcast_tag_status[podcast_name] = tag_values
            
            print(f"Found {len(podcast_tag_status)} podcasts in database")
        except Exception as e:
            print(f"Error querying existing podcasts: {e}")
            podcast_tag_status = {}
    
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
                task = process_podcast(podcast_name, genre, tags, db_path, podcast_tag_status)
                tasks.append(task)
        
        # Process podcasts concurrently with limits
        print(f"Processing {len(tasks)} podcasts with {CONCURRENT_REQUESTS} concurrent requests")
        for i, batch in enumerate([tasks[i:i+CONCURRENT_REQUESTS] for i in range(0, len(tasks), CONCURRENT_REQUESTS)]):
            print(f"Processing batch {i+1}/{(len(tasks) + CONCURRENT_REQUESTS - 1) // CONCURRENT_REQUESTS}")
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
    print("Podcast Tags:", podcast_scores)

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
