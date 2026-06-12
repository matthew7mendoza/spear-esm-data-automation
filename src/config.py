from pydantic import BaseModel, Field

class AnswerPair(BaseModel):
    question: str = Field(description = "The exact form question.")
    answer: str = Field(description = "The extracted answer.")

class FormResponses(BaseModel):
    extracted_answers: list[AnswerPair] = Field(
        description = "List mapping the exact form question to the extracted answer."
    )

    missing_information: list[str] = Field(
        description = "List of exact questions from the prompt that could not be answered using the text."

    )

DOCUMENT_TEMPLATES = {
    "DMP": {

        "questions": [
            "1. Why is the rabbit evil?\n",
            "2. What does the sun represent?\n",
            '3. Are the "other animals" explicitly afraid of the rabbit?'
        ],
        "schema": FormResponses
    },
}