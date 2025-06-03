import google.generativeai as genai

# Configure API
API_KEY = "AIzaSyCsti0qnCEKOgzAnG_w41IfMNMxkyl3ysw"
genai.configure(api_key=API_KEY)

print("Available Gemini models:")
print("=" * 50)

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"Model: {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
            print(f"  Input Token Limit: {model.input_token_limit}")
            print(f"  Output Token Limit: {model.output_token_limit}")
            print(f"  Supported Methods: {model.supported_generation_methods}")
            print("-" * 40)
except Exception as e:
    print(f"Error listing models: {e}")
