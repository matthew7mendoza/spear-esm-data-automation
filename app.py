"""
Streamlit front end
takes files and gives to back end
"""

import logging 
import streamlit as st
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"

MODEL_CONFIGURATIONS = {
    "Gemini": "gemini",
    "Nvidia": "nemotron"
}

def fetch_server_templates() -> list[str]:
    """
    Asks backend for list of available document forms to fill out
    """

    try:
        response = requests.get(f"{BACKEND_URL}/api/templates", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as error:
        logger.warning(f"Could not get templates from the worker program: {error}")

    # Must fix this hard coding later
    return ["DMP", "README"]


def send_generation_request(
    target_document: str,
    chosen_engine: str,
    uploaded_files: list
) -> None:
    """
    Packs up the loaded files and sends them to backend to be processed
    """

    file_payload = [
        ("files", (file.name, file.getvalue(), file.type))
        for file in uploaded_files
    ]

    data_payload = {
        "target_doc": target_document,
        "model_provider": MODEL_CONFIGURATIONS[chosen_engine]
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/generate",
            data = data_payload,
            files = file_payload,
            timeout=60
        )
        if response.status_code == 200:
            payload_data = response.json()
            st.session_state.generator_report = payload_data["report"]
            st.session_state.source_context = payload_data["source_context"]
            st.success("Answers successfully written!")
        else:
            st.error(
                f"Backend processing failure: {response.json().get('detail')}"
            )
    except requests.exceptions.RequestException as network_error:
        st.error(f"Could not reach background API layer... Is uvicorn running? Error: {network_error}")


def send_audit_request(
    chosen_engine: str,
    answers: dict,
    judge_iterations: int
) -> None:
    """
    Sends the current answers back to the background worker program 
    to run accuracy test, then displays final scores on the screen
    """

    audit_payload = {
        "source_context": st.session_state.source_context,
        "answers": answers,
        "iterations": judge_iterations
    }

    parameters = {"model_provider": MODEL_CONFIGURATIONS[chosen_engine]}

    try:
        audit_response = requests.post(
            f"{BACKEND_URL}/api/audit",
            json=audit_payload,
            params=parameters,
            timeout=120
        )

        if audit_response.status_code == 200:
            metrics = audit_response.json()
            st.success("Audit complete!")
            kappa_score = metrics.get("metadata", {}).get("global_gwets_ac1", 0.0)
            st.metric("Agreement score (Gwet's AC1)", kappa_score)
            st.dataframe(
                metrics.get("item_level_stability_metrics", []),
                use_container_width=True
            )
        else:
            st.error(
                f"Audit server error: {audit_response.json().get('detail')}"
            )
    except requests.exceptions.RequestException as network_error:
        st.error(f"Communication loss with audit server: {network_error}")


def render_answers_and_missing_sections() -> None:
    """
    Column for the answers that the AI found, one for the information the AI 
    could not find
    """

    st.markdown("---")
    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Extracted Answers")
        answers = st.session_state.generator_report.get("extracted_answers", {})
        for question, answer in answers.items():
            st.markdown(f"**{question}**\n> {answer}")
        
    with right_column:
        st.subheader("Missing Information")
        missing = st.session_state.generator_report.get("missing_information", [])
        if not missing:
            st.success("The AI found answers to all questions for this template!")
        for missing_question in missing:
            st.error(f"- {missing_question}")


def main() -> None:
    """
    Main
    """

    st.set_page_config(page_title="ESM Data Automation", layout="wide")
    st.title("ESM Data Automation")
    st.markdown("Automatically answer templates w/ uploaded info + check for accuracy using AI")

    if "generator_report" not in st.session_state:
        st.session_state.generator_report = None
    if "source_context" not in st.session_state:
        st.session_state.source_context = None
    
    st.sidebar.header("Settings")
    chosen_engine = st.sidebar.selectbox("Select AI Model", list(MODEL_CONFIGURATIONS.keys()))
    target_document = st.sidebar.selectbox("Chose a form template to fill out", fetch_server_templates())
    judge_iterations = st.sidebar.slider("How many times should the judge test?", 2, 10, 3)

    st.header(f"1. Generate {target_document}")
    uploaded_files = st.file_uploader(
        "Drop your scientific data, READMES, publications, ect... here:",
        accept_multiple_files=True
    )

    if st.button("Read Files & Write Answers", type="primary", disabled=not uploaded_files):
        with st.spinner("Processing files..."):
            send_generation_request(target_document, chosen_engine, uploaded_files)

    if not st.session_state.generator_report:
        return
    
    render_answers_and_missing_sections()

    st.markdown("---")
    st.header("2. LLM Judge")
    st.markdown("Run the judge test to quantify accuracy of {target_document} output")

    if st.button("Run Stability Test"):
        with st.spinner(f"Requesting {judge_iterations} concurrent background audit passes..."):
            current_answers = st.session_state.generator_report.get("extracted_answers", {})
            send_audit_request(chosen_engine, current_answers, judge_iterations)

if __name__ == "__main__":
    main()