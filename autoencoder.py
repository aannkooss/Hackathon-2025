import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
import sqlite3
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics.pairwise import cosine_similarity
import os
import sys

# --- Configuration ---
DB_PATH = 'podcasts.db'
VALIDATION_CSV_PATH = 'validation_data.csv' # Your validation file
N_EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
LATENT_DIM = 32  # Size of the compressed representation (bottleneck layer)
RECOMMENDATIONS_K = 5 # Number of recommendations to generate/validate
MODEL_DIR = 'model'  # Directory to save trained models
MODEL_PATH = os.path.join(MODEL_DIR, "autoencoder_model.pt")

# --- Global variables for loaded model and data ---
_model = None
_preprocessor = None
_features_tensor = None
_name_to_idx = None
_idx_to_name = None
_all_encodings_np = None
_device = None

# --- 1. Setup Device ---
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Using MPS device.")
elif torch.cuda.is_available():
    device = torch.device("cuda")
    print("Using CUDA device.")
else:
    device = torch.device("cpu")
    print("Using CPU device.")

# --- Helper Functions ---
def ensure_dir_exists(directory):
    """Ensures that the directory exists, creates it if it doesn't."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    return directory

def load_data(db_path):
    """Loads data from the SQLite database."""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)
    try:
        conn = sqlite3.connect(db_path)
        # Use pandas for easier reading and type inference
        query = "SELECT * FROM podcasts"
        df = pd.read_sql_query(query, conn)
        conn.close()
        print(f"Loaded {len(df)} podcasts from {db_path}")
        # Basic sanity check for expected columns (optional but good)
        if 'podcast_name' not in df.columns:
             print("Error: 'podcast_name' column missing in database.")
             sys.exit(1)
        return df
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during data loading: {e}")
        sys.exit(1)

def preprocess_data(df):
    """Preprocesses the DataFrame: handles categorical, scales numerical."""
    df_processed = df.copy()
    df_processed = df_processed.set_index('podcast_name') # Use names as index temporarily

    # Identify column types based on provided SQL schema
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

    # Verify columns exist in the dataframe
    all_feature_cols = float_cols + binary_cols + categorical_cols
    missing_cols = [col for col in all_feature_cols if col not in df_processed.columns]
    if missing_cols:
        print(f"Warning: The following expected feature columns are missing: {missing_cols}")
        # Decide how to handle: error out or proceed without them
        # For now, let's update the lists to only include present columns
        float_cols = [col for col in float_cols if col in df_processed.columns]
        binary_cols = [col for col in binary_cols if col in df_processed.columns]
        categorical_cols = [col for col in categorical_cols if col in df_processed.columns]

    # Check for NaNs and fill or drop
    if df_processed[float_cols + binary_cols].isnull().values.any():
        print("Warning: Found NaN values in feature columns. Filling with 0 for binary and mean for float.")
        for col in float_cols:
             if df_processed[col].isnull().any():
                df_processed = df_processed.dropna(subset=[col])
        for col in binary_cols:
             if df_processed[col].isnull().any():
                 df_processed[col] = df_processed[col].fillna(0) # Assume missing tag means 0
        podcast_names = df_processed.index.tolist() # Save podcast names for later use

    # Define preprocessing steps
    # Use handle_unknown='ignore' for OHE in case validation data has unseen genres
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', MinMaxScaler(), float_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols),
            ('bin', 'passthrough', binary_cols) # Binary cols are already 0/1
        ],
        remainder='drop' # Drop any columns not specified (like the original index)
    )

    # Fit and transform the data
    features_processed = preprocessor.fit_transform(df_processed[float_cols + categorical_cols + binary_cols])

    # Get feature names after transformation (important for model input size)
    feature_names_out = preprocessor.get_feature_names_out()
    print(f"Processed data shape: {features_processed.shape}")
    print(f"Number of features after preprocessing: {features_processed.shape[1]}")

    # Convert to PyTorch tensor
    features_tensor = torch.tensor(features_processed, dtype=torch.float32)

    # Create mapping from name to index
    name_to_idx = {name: i for i, name in enumerate(podcast_names)}
    idx_to_name = {i: name for i, name in enumerate(podcast_names)}

    return features_tensor, name_to_idx, idx_to_name, podcast_names, features_processed.shape[1]

# --- 3. Autoencoder Model ---
class Autoencoder(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim),
            nn.ReLU() # Or Tanh(), or nothing depending on desired latent space properties
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim),
            nn.Sigmoid() # Use Sigmoid because input features are scaled to [0, 1]
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

    def encode(self, x):
        """Encodes input data into the latent space."""
        return self.encoder(x)

# --- 4. Training Function ---
def train_model(model, dataloader, n_epochs, learning_rate, device):
    """Trains the autoencoder."""
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    model.train() # Set model to training mode

    print("\n--- Starting Training ---")
    for epoch in range(n_epochs):
        epoch_loss = 0.0
        for batch_features, in dataloader: # Dataloader yields tuples
            batch_features = batch_features.to(device)

            # Forward pass
            outputs = model(batch_features)
            loss = criterion(outputs, batch_features) # Compare reconstruction to original

            # Backward pass and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * batch_features.size(0)

        epoch_loss /= len(dataloader.dataset)
        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{n_epochs}], Loss: {epoch_loss:.4f}')
    print("--- Training Complete ---")
    return model

# --- 5. Encoding Generation ---
def generate_encodings(model, data_tensor, device):
    """Generates latent space encodings for all data."""
    model.eval() # Set model to evaluation mode
    with torch.no_grad():
        data_tensor = data_tensor.to(device)
        encodings = model.encode(data_tensor)
    return encodings.cpu().numpy() # Return as numpy array on CPU

# --- 6. Recommendation Function ---
def get_recommendations(liked_podcast_name, n_rec, all_encodings_np, name_to_idx, idx_to_name):
    """Generates recommendations based on cosine similarity in latent space."""
    if liked_podcast_name not in name_to_idx:
        print(f"Error: Podcast '{liked_podcast_name}' not found in the dataset.")
        return []

    liked_idx = name_to_idx[liked_podcast_name]
    liked_encoding = all_encodings_np[liked_idx].reshape(1, -1) # Reshape for cosine_similarity

    # Calculate cosine similarity between the liked podcast and all others
    similarities = cosine_similarity(liked_encoding, all_encodings_np)[0] # Get the single row of similarities

    # Get indices of podcasts sorted by similarity (descending)
    # Argsort gives indices that *would* sort the array
    sorted_indices = np.argsort(similarities)[::-1]

    # Get recommended names
    recommendations = []
    for idx in sorted_indices:
        if idx == liked_idx or _idx_to_name[idx] == _idx_to_name[liked_idx]: # Don't recommend the input podcast itself
            continue
        if _idx_to_name[idx] in recommendations: # Avoid duplicates
            continue
        if similarities[idx] == 1.0: # Skip if similarity is 1 (exact match)
            continue
        if len(recommendations) < n_rec:
            recommendations.append(idx_to_name[idx])
        else:
            break

    return recommendations

# --- 7. Validation Function ---
def validate_model(model, validation_csv_path, all_encodings_np, name_to_idx, idx_to_name, k):
    """Validates the model against the ground truth CSV using Precision@k."""
    if not os.path.exists(validation_csv_path):
        print(f"Warning: Validation file not found at {validation_csv_path}. Skipping validation.")
        return None

    try:
        val_df = pd.read_csv(validation_csv_path)
    except Exception as e:
        print(f"Error reading validation CSV: {e}. Skipping validation.")
        return None

    print("\n--- Starting Validation ---")
    all_precisions = []

    for col in val_df.columns:
        start_podcast = col
        ground_truth = val_df[col].dropna().tolist() # Get ground truth recommendations for this starter

        if not ground_truth:
            print(f"Skipping '{start_podcast}' in validation: No ground truth recommendations provided.")
            continue

        if start_podcast not in name_to_idx:
            print(f"Warning: Starting podcast '{start_podcast}' from validation file not found in main dataset. Skipping.")
            continue

        # Generate recommendations using the model
        model_recommendations = get_recommendations(
            start_podcast, k, all_encodings_np, name_to_idx, idx_to_name
        )

        if not model_recommendations:
            # Handles case where get_recommendations failed or returned empty
             print(f"Could not generate recommendations for '{start_podcast}'. Precision is 0.")
             precision_at_k = 0.0

        else:
            # Calculate Precision@k
            # Number of relevant items recommended / number of items recommended (k)
            relevant_and_recommended = set(model_recommendations) & set(ground_truth)
            precision_at_k = len(relevant_and_recommended) / k
            all_precisions.append(precision_at_k)

            print(f"  Starter: '{start_podcast}'")
            print(f"    Ground Truth (Top {len(ground_truth)}): {ground_truth}")
            print(f"    Model Recs (Top {k}): {model_recommendations}")
            print(f"    Precision@{k}: {precision_at_k:.4f}")

    if not all_precisions:
        print("No valid comparisons could be made during validation.")
        mean_precision = 0.0
    else:
        mean_precision = np.mean(all_precisions)
        print(f"\n--- Validation Complete ---")
        print(f"Average Precision@{k} across {len(all_precisions)} starting podcasts: {mean_precision:.4f}")

    return mean_precision

# --- 8. Save Model Function ---
def save_model(model, model_dir, model_name="autoencoder_model.pt"):
    """Saves the trained model to the specified directory."""
    ensure_dir_exists(model_dir)
    model_path = os.path.join(model_dir, model_name)
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")
    return model_path

# --- Helper Functions for Inference API ---
def load_model_for_inference():
    """
    Loads the trained model and preprocessed data into memory for inference.
    This function should be called once when the server starts.
    
    Returns:
        bool: True if model was successfully loaded, False otherwise
    """
    global _model, _preprocessor, _features_tensor, _name_to_idx, _idx_to_name, _all_encodings_np, _device
    
    # If model is already loaded, return immediately
    if _model is not None:
        return True
    
    # Set up device
    if torch.backends.mps.is_available():
        _device = torch.device("mps")
        print("Using MPS device for inference.")
    elif torch.cuda.is_available():
        _device = torch.device("cuda")
        print("Using CUDA device for inference.")
    else:
        _device = torch.device("cpu")
        print("Using CPU device for inference.")
    
    try:
        # Load data from database
        podcast_df = load_data(DB_PATH)
        if podcast_df is None:
            print("Failed to load podcast data.")
            return False
        
        # Preprocess data and save the preprocessor
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
        
        podcast_names = podcast_df['podcast_name'].tolist()
        df_processed = podcast_df.copy().set_index('podcast_name')
        
        # Create the preprocessor
        _preprocessor = ColumnTransformer(
            transformers=[
                ('num', MinMaxScaler(), float_cols),
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols),
                ('bin', 'passthrough', binary_cols)
            ],
            remainder='drop'
        )
        
        # Fit the preprocessor on the entire dataset
        _preprocessor.fit(df_processed[float_cols + categorical_cols + binary_cols])
        
        # Transform the data
        features_processed = _preprocessor.transform(df_processed[float_cols + categorical_cols + binary_cols])
        
        # Get feature names and dimensions
        input_dim = features_processed.shape[1]
        print(f"Model input dimensions: {input_dim}")
        
        # Convert to PyTorch tensor
        _features_tensor = torch.tensor(features_processed, dtype=torch.float32)
        
        # Create mappings
        _name_to_idx = {name: i for i, name in enumerate(podcast_names)}
        _idx_to_name = {i: name for i, name in enumerate(podcast_names)}
        
        # Initialize the model
        _model = Autoencoder(input_dim=input_dim, latent_dim=LATENT_DIM).to(_device)
        
        # Check if model file exists and attempt to load it
        model_loaded = False
        if os.path.exists(MODEL_PATH):
            try:
                # Try to load model weights
                _model.load_state_dict(torch.load(MODEL_PATH, map_location=_device))
                model_loaded = True
                print("Existing model loaded successfully.")
            except Exception as e:
                print(f"Error loading saved model: {str(e)}")
                print("Will retrain the model with current data dimensions...")
                model_loaded = False
        
        # If model couldn't be loaded, train a new one
        if not model_loaded:
            print("Training new model to match current data dimensions...")
            # Prepare DataLoader
            dataset = TensorDataset(_features_tensor)
            dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
            
            # Train the model
            train_model(_model, dataloader, N_EPOCHS, LEARNING_RATE, _device)
            
            # Save the trained model
            ensure_dir_exists(MODEL_DIR)
            torch.save(_model.state_dict(), MODEL_PATH)
            print(f"New model saved to {MODEL_PATH}")
        
        # Set to evaluation mode
        _model.eval()
        
        # Generate encodings for all podcasts
        print("Generating latent space encodings for recommendations...")
        _all_encodings_np = generate_encodings(_model, _features_tensor, _device)
        
        print("Model and data successfully loaded for inference.")
        return True
        
    except Exception as e:
        import traceback
        print(f"Error loading model for inference: {str(e)}")
        print(traceback.format_exc())
        return False

def get_similar_podcasts(input_data, top_k=5):
    """
    Get podcast recommendations based on either:
    1. A podcast name that exists in the database
    2. A feature vector representing podcast characteristics
    
    Args:
        input_data: Either a string with podcast name or a dictionary/list of podcast features
        top_k: Number of recommendations to return
    
    Returns:
        list: List of dictionaries containing recommended podcast names and similarity scores
        None: If an error occurs
    """
    global _model, _all_encodings_np, _name_to_idx, _idx_to_name, _device, _preprocessor
    
    # Check if model is loaded
    if _model is None or _preprocessor is None:
        success = load_model_for_inference()
        if not success:
            return {"error": "Failed to load the model."}
    
    try:
        # Case 1: Input is a podcast name
        if isinstance(input_data, str):
            if input_data not in _name_to_idx:
                return {"error": f"Podcast '{input_data}' not found in the database."}
            
            liked_idx = _name_to_idx[input_data]
            input_encoding = _all_encodings_np[liked_idx].reshape(1, -1)
            
        # Case 2: Input is a feature vector (dictionary or list)
        else:
            if isinstance(input_data, dict):
                # Define the feature columns we expect
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
                
                # Create a DataFrame with the input data
                features_dict = {}
                
                # Process float columns
                for col in float_cols:
                    features_dict[col] = input_data.get(col, 5.0)  # Default to middle value if missing
                    
                # Process binary columns
                for col in binary_cols:
                    features_dict[col] = input_data.get(col, 0)  # Default to 0 if missing
                    
                # Process categorical columns
                for col in categorical_cols:
                    features_dict[col] = input_data.get(col, 'unknown')  # Default to unknown if missing
                
                # Create dataframe with single row
                df = pd.DataFrame([features_dict])
                
                # Use the already fit preprocessor to transform the input
                # This ensures dimensionality matches what the model expects
                features_processed = _preprocessor.transform(df)
                
                # Convert to tensor
                input_tensor = torch.tensor(features_processed, dtype=torch.float32).to(_device)
                
                # Get encoding
                with torch.no_grad():
                    input_encoding = _model.encode(input_tensor).cpu().numpy()
                    
            elif isinstance(input_data, list):
                # Convert list to tensor directly - assuming correct order matching the model's input
                input_tensor = torch.tensor(input_data, dtype=torch.float32).unsqueeze(0).to(_device)
                
                # Get encoding
                with torch.no_grad():
                    input_encoding = _model.encode(input_tensor).cpu().numpy()
                    
            else:
                return {"error": "Input data must be either a podcast name string or a feature vector (dict or list)."}
                
        # Calculate similarities and get recommendations
        similarities = cosine_similarity(input_encoding, _all_encodings_np)[0]
        
        # Get indices of podcasts sorted by similarity (descending)
        sorted_indices = np.argsort(similarities)[::-1]
        
        # Get top recommendations (excluding the input podcast if it's in the database)
        recommendations = []

        input_podcasts = []
        if isinstance(input_data, str):
            _split = input_data.split(",")
            for _podcast in _split:
                input_podcasts.append(_podcast.strip())
        
        recc_names = []
        for idx in sorted_indices:
            # Skip if the podcast is already in recommendations
            if _idx_to_name[idx] in recc_names:
                continue
            # Skip if input podcast list is not empty and the current podcast is in it
            if input_podcasts and _idx_to_name[idx] in input_podcasts:
                continue
            # Skip if the podcast is already in recc_names
            if _idx_to_name[idx] in recc_names:
                continue
            # skip if similarity is 1
            if similarities[idx] == 1.0:
                continue
                
            recc_names.append(_idx_to_name[idx])
            # Add to recommendations
            if len(recommendations) < top_k:
                recommendations.append({
                    "podcast_name": _idx_to_name[idx],
                    "similarity_score": float(similarities[idx])
                })
            else:
                break

        # Then reduce the length of the recommendations to the min(len(reccomendations), 5)
        num_recs = min(len(recommendations), 5)
        recommendations = recommendations[:num_recs]
                
        return recommendations
        
    except Exception as e:
        import traceback
        print(f"Error in get_similar_podcasts: {str(e)}")
        print(traceback.format_exc())
        return {"error": str(e)}

# --- 9. Main Execution ---
if __name__ == "__main__":
    # Load and preprocess
    podcast_df = load_data(DB_PATH)
    if podcast_df is None:
         sys.exit(1) # Exit if data loading failed

    features_tensor, name_to_idx, idx_to_name, podcast_names, input_dim = preprocess_data(podcast_df)

    # Prepare DataLoader
    dataset = TensorDataset(features_tensor)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # Initialize and train the model
    model = Autoencoder(input_dim=input_dim, latent_dim=LATENT_DIM).to(device)
    print(f"\nModel Architecture:\n{model}")
    train_model(model, dataloader, N_EPOCHS, LEARNING_RATE, device)
    
    # Save the trained model
    model_path = save_model(model, MODEL_DIR)

    # Generate encodings for all podcasts
    print("\nGenerating latent space encodings...")
    all_encodings_np = generate_encodings(model, features_tensor, device)
    print(f"Generated encodings shape: {all_encodings_np.shape}")

    # --- Example Usage ---
    example_podcast = podcast_names[0] if podcast_names else None # Use the first podcast as an example
    if example_podcast:
        print(f"\n--- Example Recommendation ---")
        recommendations = get_recommendations(
            example_podcast, RECOMMENDATIONS_K, all_encodings_np, name_to_idx, idx_to_name
        )
        print(f"Recommendations for '{example_podcast}':")
        if recommendations:
            for i, rec in enumerate(recommendations):
                print(f"  {i+1}. {rec}")
        else:
            print("  No recommendations generated (maybe the podcast wasn't found or an error occurred).")

    # --- Run Validation ---
    validation_score = validate_model(
        model, VALIDATION_CSV_PATH, all_encodings_np, name_to_idx, idx_to_name, RECOMMENDATIONS_K
    )
    if validation_score is not None:
       print(f"\nFinal Validation Score (Mean Precision@{RECOMMENDATIONS_K}): {validation_score:.4f}")

    print("\nScript finished.")
