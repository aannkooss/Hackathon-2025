import argparse
import json
import sys
import os
import uvicorn
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

# Import the inference functions from autoencoder.py
try:
    from autoencoder import load_model_for_inference, get_similar_podcasts
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
    podcasts: List[str]

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[""],  # or ["http://localhost:3000/"] to be more restrictive
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=["*"],
)

# API routes
@app.post("/api/interests")
async def process_interests(request: InterestsRequest = Body(...)):
    """
    Process the interests provided by the user and print them
    
    Args:
        request: The JSON request body containing user interests
        
    Returns:
        dict: A simple acknowledgment of receipt
    """
    # Print the received JSON data
    print("\nReceived interests data:")
    print(json.dumps(request.data, indent=2))
    
    return {"status": "success", "message": "Interests received"}

@app.post("/api/podcast_input")
async def process_podcast_input(request: PodcastInputRequest = Body(...)):
    """
    Process a list of podcast names provided by the user
    
    Args:
        request: The JSON request body containing a list of podcast names
        
    Returns:
        dict: A simple acknowledgment of receipt
    """
    # Print the received podcast list
    print("\nReceived podcast input:")
    for i, podcast in enumerate(request.podcasts):
        print(f"  {i+1}. {podcast}")
    
    return {"status": "success", "message": f"Received {len(request.podcasts)} podcasts"}

def run_inference(podcast_name, top_k=5):
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
