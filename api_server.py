import argparse
import json
import sys
import os
import uvicorn
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import time
from dotenv import load_dotenv
from google import genai
from search_extract_podcast_slug import extract_all_names

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("GOOGLE_API_KEY_NIK")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")

# Import the inference functions from autoencoder.py
try:
    from autoencoder import load_model_for_inference, get_similar_podcasts
    load_model_for_inference()
except ImportError:
    print("Error: Could not import required functions from autoencoder.py")
    print("Make sure you're running this script from the same directory as autoencoder.py")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(title="Podcast Recommendation API")

# Define the request model for interests
class InterestsRequest(BaseModel):
    # This is a flexible model that can accept any JSON content
    data: Dict[str, Any]

# Define the request model for podcast input
class PodcastInputRequest(BaseModel):
    podcasts: str  # Changed from List[str] to str

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000/"] to be more restrictive
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
# Request model
class InterestsRequest(BaseModel):
    interests1: str
    interests2: str

@app.post("/api/interests")
async def process_interests(request: InterestsRequest):
    received = request.model_dump()
    print("Received:", received)  # Or access fields individually
    
    # Get the text from the file prompt_analyze_user_input.txt
    first_prompt_file = "prompt_analyze_user_input.txt"
    second_prompt_file = "prompt_genre_user_input.txt"
    with open(first_prompt_file, "r") as file:
        prompt_1 = file.read()
    with open(second_prompt_file, "r") as file:
        prompt_2 = file.read()
    
    interests_prompt = "First user interest: " + request.interests1 + "\n" + "Second user interest: " + request.interests2 + "\n" + prompt_1

    genre_prompt = "First user interest: " + request.interests1 + "\n" + "Second user interest: " + request.interests2 + "\n" + prompt_2
    
    # Initialize Gemini client
    try:
        client = genai.Client(api_key=API_KEY)
        
        print("Sending interests prompt to Gemini LLM...")
        start_time = time.time()
        
        # Send the first prompt to the LLM
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=interests_prompt,
        )
        
        # Extract the response text
        result_text = response.text
        print(f"LLM interests response received in {time.time() - start_time:.2f} seconds")
        
        # Now send the second prompt for genre classification
        print("Sending genre prompt to Gemini LLM...")
        genre_start_time = time.time()
        
        genre_response = client.models.generate_content(
            model=LLM_MODEL,
            contents=genre_prompt,
        )
        
        genre_text = genre_response.text
        print(f"LLM genre response received in {time.time() - genre_start_time:.2f} seconds")
        
        # Extract genre from response
        genre = None
        try:
            # Find JSON in the genre response
            first_genre_idx = genre_text.find('{')
            last_genre_idx = genre_text.rfind('}')
            
            if first_genre_idx != -1 and last_genre_idx != -1:
                genre_json_text = genre_text[first_genre_idx:last_genre_idx+1]
                genre_data = json.loads(genre_json_text)
                genre = genre_data.get("genre")
        except json.JSONDecodeError:
            print("Warning: Could not parse genre response as JSON")
        
        # Try to parse JSON from the main interests response
        try:
            # Find JSON in the response
            first_kept_idx = result_text.find('{')
            last_kept_idx = result_text.rfind('}')
            
            if first_kept_idx != -1 and last_kept_idx != -1:
                json_text = result_text[first_kept_idx:last_kept_idx+1]
                result_data = json.loads(json_text)
                
                # Add genre to the result data
                if genre:
                    result_data["genre"] = genre
                
                # Get podcast recommendations using the feature vector from LLM
                print("Getting podcast recommendations based on feature vector...")
                recommendations = get_similar_podcasts(result_data, top_k=5)
                
                return {
                    "status": "success", 
                    "message": "Interests processed successfully",
                    "result": result_data,
                    "recommendations": recommendations
                }
            else:
                # Create a new result object with just the genre if JSON not found
                result_data = {"raw_text": result_text}
                if genre:
                    result_data["genre"] = genre
                
                return {
                    "status": "success", 
                    "message": "Interests processed successfully",
                    "result": result_data
                }
                
        except json.JSONDecodeError:
            # Create a result with the text and genre
            result_data = {"raw_text": result_text}
            if genre:
                result_data["genre"] = genre
                
            return {
                "status": "success", 
                "message": "Interests processed successfully (non-JSON response)",
                "result": result_data
            }
            
    except Exception as e:
        print(f"Error processing interests with LLM: {str(e)}")
        return {"status": "error", "message": f"Error processing interests: {str(e)}"}

@app.post("/api/podcast_input")
async def process_podcast_input(request: PodcastInputRequest = Body(...)):
    """
    Process a list of podcast names provided by the user as a comma-separated string
    
    Args:
        request: The JSON request body containing a string of podcast names
        
    Returns:
        dict: Results including recommendations based on the average features of provided podcasts
    """
    # Print the received podcast list
    print("\nReceived podcast input:")
    # No change in how extract_all_names is called since it already handles strings
    podcasts = extract_all_names(request.podcasts)
    for i, podcast in enumerate(podcasts):
        print(f"  {i+1}. {podcast}")
    
    # Get feature vectors for each podcast from the database
    found_podcasts = []
    not_found = []
    
    try:
        import sqlite3
        import pandas as pd
        from collections import Counter
        
        # Connect to the database
        conn = sqlite3.connect('podcasts.db')
        
        # Retrieve feature vectors for each podcast
        for podcast_name in podcasts:
            query = f"SELECT * FROM podcasts WHERE podcast_name = ? COLLATE NOCASE"
            df = pd.read_sql_query(query, conn, params=(podcast_name,))
            
            if len(df) > 0:
                found_podcasts.append(df.iloc[0].to_dict())
                print(f"Found podcast '{podcast_name}' in database")
            else:
                not_found.append(podcast_name)
                print(f"Podcast '{podcast_name}' not found in database")
        
        conn.close()
        
        # Check if we found any podcasts
        if not found_podcasts:
            return {
                "status": "error",
                "message": "None of the provided podcasts were found in our database",
                "not_found": not_found
            }
        
        # Calculate average feature vector
        # Identify numeric columns and categorical columns
        float_cols = ["Comedic","Controversy","Consistency","Thought Provoking","Bias",
                      "Expressivness","Exciting","Pacing","Level of fiction","Narrative",
                      "Originality","Production Quality","Positivity","Personal",
                      "Educational","Conservative","Progressive","Equity - minded",
                      "Adult Content","Explicit Language","Self Improvement",
                      "Family oriented","Historical Focus","Modern Focus"]
        binary_cols = ["Finance", "Romance", "Self-Improvment", "Interviews", "Video Games",
                       "Comedy", "True Crime", "Technology", "Politics", "History",
                       "Sports", "Health and Wellness", "Education", "Business",
                       "Storytelling", "Art and Design", "Literature", "Food and Drink",
                       "Travel", "Environment", "Spirituality", "Parenting",
                       "Relationships", "Lifestyle", "Entrepreneurship", "Documentary"]
        categorical_cols = ['genre']
        
        # Initialize average feature vector
        avg_features = {}
        
        # Average numeric features
        for col in float_cols + binary_cols:
            values = [float(podcast.get(col, 0)) for podcast in found_podcasts if col in podcast]
            if values:
                avg_features[col] = sum(values) / len(values)
            else:
                avg_features[col] = 0.0
        
        # Get most common genre
        genre_values = [podcast.get('genre', 'unknown') for podcast in found_podcasts if 'genre' in podcast]
        if genre_values:
            most_common_genre = Counter(genre_values).most_common(1)[0][0]
            avg_features['genre'] = most_common_genre
        else:
            avg_features['genre'] = 'unknown'
        
        # Get recommendations based on average feature vector
        print("Getting podcast recommendations based on average feature vector...")
        recommendations = get_similar_podcasts(avg_features, top_k=16)
        
        return {
            "status": "success",
            "message": f"Processed {len(found_podcasts)} podcasts",
            "found_podcasts": [p.get('podcast_name', 'Unknown') for p in found_podcasts],
            "not_found": not_found,
            "averaged_features": avg_features,
            "recommendations": recommendations
        }
        
    except Exception as e:
        import traceback
        print(f"Error processing podcast input: {str(e)}")
        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"Error processing podcasts: {str(e)}",
            "not_found": not_found
        }

def run_inference(podcast_name, top_k=16):
    """
    Load the model and run inference for a specific podcast
    
    Args:
        podcast_name (str): Name of the podcast to find recommendations for
        top_k (int): Number of recommendations to return
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Load the model (will be cached in memory after first call)
    success = load_model_for_inference()
    if not success:
        print("Failed to load the model.")
        return False
    
    # Get recommendations
    recommendations = get_similar_podcasts(podcast_name, top_k)
    
    # Check for errors
    if isinstance(recommendations, dict) and "error" in recommendations:
        print(f"Error: {recommendations['error']}")
        return False
    
    # Print results
    print(f"\nTop {len(recommendations)} recommendations for '{podcast_name}':")
    print("-" * 50)
    for i, rec in enumerate(recommendations):
        print(f"{i+1}. {rec['podcast_name']} (Similarity: {rec['similarity_score']:.4f})")
    
    return True

def start_server(port=2020):
    """Start the FastAPI server on the specified port"""
    # Preload the model so it's ready when API requests come in
    print("Loading model for API server...")
    load_model_for_inference()
    
    # Start the uvicorn server
    print(f"Starting API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)

def main():
    """Main function to parse arguments and run the appropriate functions"""
    parser = argparse.ArgumentParser(description="Podcast Recommendation API Server")
    
    # Add server mode
    parser.add_argument("--server", action="store_true", help="Run as API server")
    parser.add_argument("--port", type=int, default=2020, help="Port to run the server on")
    
    # Add inference mode
    parser.add_argument("--infer", type=str, help="Run inference for a specific podcast name")
    parser.add_argument("--top-k", type=int, default=5, help="Number of recommendations to return")
    
    args = parser.parse_args()
    
    # Run in inference mode
    if args.infer:
        success = run_inference(args.infer, args.top_k)
        if not success:
            sys.exit(1)
    
    # Run in server mode
    elif args.server:
        start_server(args.port)
    
    # No mode specified
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
