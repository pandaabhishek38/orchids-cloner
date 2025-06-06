import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

# Load API key from .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
# openai.api_key = os.getenv("OPENAI_API_KEY")

def scrape_website(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        for tag in soup(["script", "noscript", "iframe", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        title = soup.title.string if soup.title else "Untitled Website"

        context = f"Website Title: {title}\n\nPage Text:\n{text[:4000]}"
        return context

    except Exception as e:
        return f"Error: {str(e)}"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_html_from_context(context: str) -> str:
    prompt = f"""
You are a helpful frontend engineer. Based on the description below, generate a clean, visually similar static HTML page using basic inline styles.

--- WEBSITE CONTEXT START ---
{context}
--- WEBSITE CONTEXT END ---

Output only valid HTML. Do not include <script> tags.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"<html><body><h2>LLM Error</h2><p>{str(e)}</p></body></html>"
