"""
FastAPI backend
uvicorn api:app --reload --port 8000
"""

import tempfile
import asyncio 
from pathlib import Path
from typing import Any
from fastapi import (
    FastAPI, 
    UploadFile,
    File,
    Form,
    HTTPException,
    Query
)
from pydantic import BaseModel
import yaml
import json

from src.providers import get_provider
from src.generator import DocumentGenerator
from src.judge import LLMJudge
from src.document import extract_text, EXTRACTOR_MAP

app = FastAPI(
    title="ESM Data Automation API",
    description="backend"
)

class AuditRequest(BaseModel):
    """
    Pydantic schema handle input validation for JSON endpoints
    """

    source_context: str
    answers: dict[str, Any]
    iterations: int = 3

@app.get("/api/templates")
def get_templates():
    """
    Gets available template keys from templates.yaml
    """

    template_path = Path("src/templates.yaml")
    if not template_path.exists():
        # Will fix this hardcode later
        return ["DMP", "README"]
        
    with open(template_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
        return list(data.get("DOCUMENT_TEMPLATES", {}).keys())
        
@app.post("/api/generate")
async def generate_document(
    target_doc: str = Form(...),
    model_provider: str = Form("gemini"),
    files: list[UploadFile] = File(...)
):
    """
    Accepts file streams, puts in temporary directory,
    triggers the LLM generator
    """

    try:
        provider_instance = get_provider(name=model_provider)
        generator = DocumentGenerator(provider=provider_instance)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"LLM Provider Initialization Failure: {error}")
    
    with tempfile.TemporaryDirectory() as temp_directory:
        temp_path = Path(temp_directory)

        for uploaded_file in files:
            file_disk_path = temp_path / Path(uploaded_file.filename).name
            content = await uploaded_file.read()
            file_disk_path.write_bytes(content)
        
        try:
            report = await asyncio.to_thread(
                generator.generate_draft_from_directory, 
                target_doc,
                temp_path
            )

            def parse_source_files():
                return [
                    f"--- SOURCE CONTEXT ASSET: {file_path.name} ---\n{extract_text(file_path)}"
                    for file_path in temp_path.iterdir()
                    if file_path.suffix.lower() in EXTRACTOR_MAP
                ]
            
            source_blocks = await asyncio.to_thread(parse_source_files)
            combined_text = "\n\n".join(source_blocks)

            return {
                "report": report,
                "source_context": combined_text
            }
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Generation processing error: {str(error)}")


@app.post("/api/audit")
async def run_audit(payload: AuditRequest, model_provider: str = Query("gemini")):
    """
    Run stability test w/o blocking primary application
    """

    try:
        provider_instance = get_provider(name=model_provider)
        judge = LLMJudge(provider=provider_instance)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"LLM Judge Provider Failure: {error}")
    
    answers_as_text = json.dumps(payload.answers, indent=2)
    try:
        metrics = await judge.run_stability_stress_test_async(
            source_content=payload.source_context,
            paste_content=answers_as_text,
            prefix_label="API_EVAL",
            i_iterations=payload.iterations
        )
        return metrics
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Stability Audit Failure: {str(error)}")
    