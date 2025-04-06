# Hackathon-2025

## Project Overview
A personalized podcast recommendation system that uses machine learning to suggest podcasts based on user interests or previously enjoyed podcasts. The system combines natural language processing with an autoencoder model to provide accurate podcast recommendations tailored to individual preferences.

## Architecture
- **Backend**: Python-based machine learning system with FastAPI server
- **Frontend**: React-based web application with animated UI components
- **Data Processing**: Autoencoder model for podcast feature extraction and similarity matching

## Features
- Two recommendation pathways:
  - Interest-based: Users describe their interests and preferences
  - Podcast-based: Users list podcasts they already enjoy
- Natural language processing of user inputs via Google Gemini
- Interactive, animated user interface with step-by-step flow
- REST API to connect the ML backend with the React frontend

## Instructions for starting the backend:
Clone the repo
`python -m venv venv`
`source venv/bin/activate`
`pip install -r requirements.txt`
`python autoencoder.py` - Train the autoencoder
`python api_server.py --server` - Start the API server

## Instructions for starting the frontend:
Clone the repo
`cd my-app`
`npm install`
`npm start` - Start the frontend

## API Endpoints
- `/api/interests` - Process user interests and return podcast recommendations
- `/api/podcast_input` - Process user's favorite podcasts and return similar recommendations

## Tools used:
- Google Gemini for synthetic data generation
- OpenAI for code generation (quick implementation assistance and debugging)
- FastAPI for backend API server
- React with Framer Motion for animated frontend
- PyTorch for machine learning model development