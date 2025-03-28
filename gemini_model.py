import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("API key not found! Set GOOGLE_API_KEY in .env file.")

# Configure GenAI with secure API key
genai.configure(api_key=api_key)

# Use a specific model
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
print("Model loaded successfully!")