import os
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Load the secret key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("Connecting to Google to fetch available models...\n")

# 2. Ask Google for the list
try:
    for model in genai.list_models():
        # We only want models that can do standard text generation
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ Found Model: {model.name}")
except Exception as e:
    print(f"Failed to connect: {e}")