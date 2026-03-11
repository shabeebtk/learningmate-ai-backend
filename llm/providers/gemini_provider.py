from google import genai
from django.conf import settings

def generate_gemini(model, prompt, temperature, max_tokens):

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text