import os
import requests
import openai
from openai import OpenAI

openai.api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai.api_key)
LIBRE_URL = os.getenv("LIBRE_URL", "https://translate.argosopentech.com")


# Toggle between libre and gpt
TRANSLATOR = os.getenv("TRANSLATOR", "libre")  # options: 'libre', 'gpt'

def translate_with_libre(text, target_lang="es"):
    try:
        res = requests.post(f"{LIBRE_URL}/translate", json={
            "q": text,
            "source": "en",
            "target": target_lang,
            "format": "text"
        }, timeout=10)
        res.raise_for_status()
        return res.json()["translatedText"]
    except Exception as e:
        print(f"[LibreTranslate Error] {e}")
        return None

def translate_with_gpt(text, model="gpt-3.5-turbo"):
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Translate the following weather alert from English to Spanish."},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OpenAI Translation Error] {e}")
        return None

def translate_to_spanish(text, use="default"):
    if not text or not text.strip():
        return ""
    
    engine = use if use != "default" else TRANSLATOR

    if engine == "libre":
        translated = translate_with_libre(text)
        if translated:
            return translated
        print("⚠️ Falling back to GPT...")
        return translate_with_gpt(text)
    elif engine == "gpt":
        return translate_with_gpt(text)
    else:
        print(f"❌ Unknown translator engine: {engine}")
        return None
