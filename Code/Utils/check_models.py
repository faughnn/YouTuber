from google import genai
import os

# Configure API client
API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=API_KEY)

print("Available Gemini models:")
print("=" * 50)

try:
    for model in client.models.list():
        print(f"Model: {model.name}")
        if hasattr(model, 'display_name'):
            print(f"  Display Name: {model.display_name}")
        if hasattr(model, 'description'):
            print(f"  Description: {model.description}")
        if hasattr(model, 'input_token_limit'):
            print(f"  Input Token Limit: {model.input_token_limit}")
        if hasattr(model, 'output_token_limit'):
            print(f"  Output Token Limit: {model.output_token_limit}")
        print("-" * 40)
except Exception as e:
    print(f"Error listing models: {e}")
