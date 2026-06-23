"""
Tracks how consistent and stable an AI's answers are across multiple runs.
"""
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Generator
from collections import Counter
import yaml
from google import genai
from google.genai import types

from src.models import MasterAuditPayloadSchema, AgentExecutionError, AgentConfigurationError
from src.metrics import(
    calculate_percentage_agreement,
    calculate_gwets_ac1,
    calculate_fleiss_kappa,
    calculate_reasoning_stability
)

logger = logging.getLogger(__name__)

class LLMJudge:
    """
    Runs tests to measure how consistently the AI gives the same answers and grades.
    """

    STRATEGY_KEYWORDS = {
        "Numeric": ["count", "word", "total", "volume", "number"],
        "Quote": ["verbatim", "string", "quote", "text", "url"]
    }

    def __init__(self, client: genai.Client):
        if not client:
            raise ValueError("An active AI client must be provided.")
        self.client = client
        self.system_instruction = self._load_judge_instructions()

    def _load_judge_instructions(self) -> str:
        """
        Loads judge system instructions from templates.yaml file
        """
        config_path = Path(__file__).parent / "templates.yaml"
        if not config_path.exists():
            raise AgentConfigurationError(f"templates.yaml file missing at path: {config_path.resolve()}")
        
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
            return data["JUDGE_INSTRUCTIONS"]
        except KeyError as key_error:
            raise AgentConfigurationError("The required key 'JUDGE_INSTRUCTIONS' was missing inside templates.yaml") from key_error
        except Exception as yaml_error:
            raise AgentConfigurationError("Failed to cleanly decode external YAML runtime templates structure.") from yaml_error


    async def execute_multi_axis_evaluation_async(self, technical_context: str, generated_paste: str) -> dict[str, Any] | None:
        """
        Asks the AI to evaluate if a copied table matches original source documentation asynchroniously
        """

        user_prompt = (
            f"[SOURCE DOCUMENT]\n{technical_context}\n\n"
            f"[COMPLIANCE TABLE TO CHECK]\n{generated_paste}"
        )

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-3.1-pro-preview",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    response_mime_type="application/json",
                    response_schema=MasterAuditPayloadSchema,
                    temperature=0.0
                )
            )

            raw_output = response.text
            if raw_output:
                try:
                    return json.loads(raw_output)
                except json.JSONDecodeError as json_error:
                    logger.error(f"Failed to parse concurrent LLM json output. error: {json_error}")
                    return None
            return None
        
        except Exception as api_error:
            logger.error("Failed to communicate with AI model during async evaluation", exc_info=True)
            return None
        
    def _yield_all_items(self, raw_runs_history: list[dict[str, Any]]) -> Generator[dict[str, Any], None, None]:
        """
        Flattens a list of past test runs to extract each question and answer item.
        """

        for run in raw_runs_history:
            for category in run.get("categories", []):
                for item in category.get("items", []):
                    yield item

    def _infer_evaluation_strategy(self, question_text: str) -> str:
        """
        Figures out of a question checks for a quote, numeric value, or assertion based on keywords.
        """

        question_lower = question_text.lower()
        for strategy, keywords in self.STRATEGY_KEYWORDS.items():
            if any(word in question_lower for word in keywords):
                return strategy
        return "Assertion"
    
    async def run_stability_stress_test_async(
        self,
        source_content: str,
        paste_content: str,
        prefix_label: str,
        i_iterations: int = 5
    ) -> dict[str, Any]:
        """
        Runs the evaluation multiple times at the same time.
        Check's if the AI's answers shift or stay stable.
        """

        tasks = [
            self.execute_multi_axis_evaluation_async(source_content, paste_content)
            for _ in range(i_iterations)
        ]

        completed_runs = await asyncio.gather(*tasks)

        raw_runs_history = [run for run in completed_runs if run is not None]
        if not raw_runs_history:
            logger.error("All instances of evaluations runs failedd. Cannot calculate LLM's stability statistics")
            return {}
        
        compiled_question_map: dict[str, dict[str, Any]] = {}
        for item in self._yield_all_items(raw_runs_history):
            question_text = item.get("question")
            if not question_text:
                continue

            if question_text not in compiled_question_map:
                compiled_question_map[question_text] = {
                    "verdicts": [],
                    "justifications": [],
                    "strategy": self._infer_evaluation_strategy(question_text)
                }
            
            compiled_question_map[question_text]["verdicts"].append(item.get("answer", "No"))
            compiled_question_map[question_text]["justifications"].append(item.get("justification", ""))

        final_metrics_report = {
            "metadata": {
                "profile_prefix": prefix_label,
                "execution_timestamp": datetime.now().isoformat(),
                "total_runs_i": len(raw_runs_history),
                "global_fleiss_kappa": 0.0
            },
            "item_level_stability_metrics": []
        }

        verdict_matrix_for_kappa = []
        for question_text, data in compiled_question_map.items():
            verdict_list = data["verdicts"]
            strategy = data["strategy"]
            verdict_matrix_for_kappa.append(verdict_list)

            final_metrics_report["item_level_stability_metrics"].append({
                "question": question_text,
                "inferred_strategy": strategy,
                "percentage_agreement_pa": round(calculate_percentage_agreement(verdict_list), 2),
                "gwets_ac1_gamma": round(calculate_gwets_ac1(verdict_list), 4),
                "reasoning_stability_r_stab": round(calculate_reasoning_stability(data["justifications"], strategy), 2),
                "raw_verdict_distribution": dict(Counter(verdict_list))
            })

        if verdict_matrix_for_kappa:
            final_metrics_report["metadata"]["global_fleiss_kappa"] = round(
                calculate_fleiss_kappa(verdict_matrix_for_kappa), 4
            )
        
        return final_metrics_report