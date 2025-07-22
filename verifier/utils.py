import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_with_gemini(text, doc_type):
    prompt = f"""
You are an intelligent document verifier. The user has uploaded a {doc_type} document. 
Extract and return the following fields as JSON:
- name
- dob (date of birth)
- document_number
- document_type (should be one of: aadhaar, pan, passport)

Here is the raw OCR text:
\"\"\"
{text}
\"\"\"
Return output in this format:
{{
  "name": "...",
  "dob": "...",
  "document_number": "...",
  "document_type": "..."
}}
If any field is missing, use null.
    """

    model = genai.GenerativeModel("gemini-1.5-pro")  # ✅ correct model name
    response = model.generate_content(prompt)
    try:
        return eval(response.text.strip())
    except Exception:
        return {
            "name": None,
            "dob": None,
            "document_number": None,
            "document_type": doc_type
        }
