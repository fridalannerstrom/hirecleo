import os
import re
import json
from openai import OpenAI

client = OpenAI()

def clean_cv_text(text, phone=None, email=None, linkedin=None):
    """Rensar kontaktuppgifter och fixar radbrytningar i CV-text."""
    if phone:
        text = re.sub(re.escape(phone), '', text)
    if email:
        text = re.sub(re.escape(email), '', text)
    if linkedin:
        text = re.sub(re.escape(linkedin), '', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'(?<=[a-zA-Z0-9äöå])\.\s+(?=[A-ZÅÄÖ])', '.\n', text)
    return text.strip()

def reformat_cv_text_with_openai(raw_text):
    """Formaterar CV-text till professionellt format."""
    prompt = f"""
You are an expert at writing CV excerpts from PDF files. Your task is to structure the text so that it is easy to read and professionally presented. Also make it shorter and more concise.

- Keep all important information
- Divide the text into headings such as: Work experience, Education, Skills, Other
- Remove unnecessary line breaks, incorrect formatting and strange spaces
- Structure it as if it were a real, nice CV
- Do not include name, email, phone number or LinkedIn in the text
- Write in English

Here is the original text:

\"\"\"{raw_text[:3000]}\"\"\"
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an experienced and skilled CV writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=2048
    )
    return response.choices[0].message.content.strip()

def extract_candidate_data_with_openai(text):
    """Anropar OpenAI för att extrahera kandidatens uppgifter i JSON-format."""
    prompt = f"""
Här är innehållet från ett CV:

\"\"\"{text[:2000]}\"\"\"

Extrahera följande information:
- Förnamn
- Efternamn
- E-postadress
- Telefonnummer
- LinkedIn-länk (om det finns)
- Lista med 3 top skills (som Python, SQL, Figma) – skriv på engelska

Returnera **endast ett JSON-objekt** med följande nycklar:
"Förnamn", "Efternamn", "E-postadress", "Telefonnummer", "LinkedIn-länk", "Top Skills"
"""
    print("🧠 Skickar prompt till GPT...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du är en duktig CV-analytiker."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=600
    )

    raw_result = response.choices[0].message.content
    print("📩 RAW OpenAI response:\n", raw_result)

    return parse_json_result(raw_result)

def extract_job_data_with_openai(text):
    """Extraherar strukturerad jobbdata från en jobbeskrivning."""
    prompt = f"""
Här är en jobbannons i textformat:

\"\"\"{text[:2000]}\"\"\"

Extrahera följande som JSON:
- Titel
- Företag
- Plats
- Anställningsform
- Beskrivning (kort, renskriven version)

Returnera **endast** ett giltigt JSON-objekt. Inga kommentarer eller extra text.
"""
    print("🧠 Skickar jobbannons till GPT...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du är en expert på att tolka jobbannonser."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=600
    )

    raw_result = response.choices[0].message.content
    print("📩 RAW OpenAI job-response:\n", raw_result)

    return parse_json_result(raw_result)

def parse_json_result(raw_result):
    """Rensar bort ```json och parsar till dict."""
    try:
        cleaned = re.sub(r"```json|```", "", raw_result).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("❌ JSONDecodeError:", e)
        raise
