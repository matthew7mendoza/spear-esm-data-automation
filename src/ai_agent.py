import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.config import DOCUMENT_TEMPLATES


env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path = env_path, override = True)

class LLM_Agent:
    def __init__(self, model_name = "gemini-3.1-pro-preview", temperature = 0.0):

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(f"API Key not found in {env_path}")

        self.client = genai.Client(api_key = api_key)
        self.model_name = model_name
        self.temperature = temperature

        # Master prompt of AI agent
        self.system_instructions = (
            "You are a strict data management assistant. Your objective is to extract information "
            "from user-provided scientific documents and metadata to accurately answer form questions "
            "for Data Management Plans, ReadMes, and DOIs. "
            "Keep answers concise and strictly technical. If the provided document does not contain "
            "the answer to a requested question, do not guess. Instead, add that exact question to the "
            "missing_information list."
            )
        
    def extract_data(self, questions_list, document_text, schema):
        """
        Feeds the text to the model and forces the output into the provided format schema.
        Transforms API's strict JSON list back into a usable Python dictionary
        """
        
        formatted_questions = "\n".join(f"- {q}" for q in questions_list)
        prompt = f"QUESTIONS TO ANSWER:\n{formatted_questions}\n\nSOURCE DOCUMENT:\n{document_text}"

        config = types.GenerateContentConfig(
            system_instruction = self.system_instructions,
            temperature = self.temperature,
            response_mime_type = "application/json",
            response_schema = schema,
        )

        response = self.client.models.generate_content(
            model = self.model_name,
            contents = prompt,
            config = config
        )

        raw_data = json.loads(response.text)
        flat_answers = {item["question"]: item["answer"] for item in raw_data["extracted_answers"]}

        return {
            "extracted_answers": flat_answers,
            "missing_information": raw_data["missing_information"]
        }


    def process_document(self, doc_type, document_text):
        config = DOCUMENT_TEMPLATES.get(doc_type.upper())

        if not config:
            raise ValueError(f"Unsupported document type: '{doc_type}'")
        
        return self.extract_data(
            questions_list = config["questions"],
            document_text = document_text,
            schema = config["schema"]
        )