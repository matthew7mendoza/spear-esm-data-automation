"""
Primary streamlit rendering
"""

import streamlit as st

from frontend.api import fetch_server_templates
from frontend.components.results import render_answers_and_missing_sections
from frontend.components.sidebar import render_historical_sidebar
from frontend.config import MODEL_CONFIGURATIONS
from frontend.services import send_audit_request, send_generation_request

__all__ = ["main"]

def _initialize_session_state() -> None:
    """
    Set up core streamlit session with explicit mutation
    """

    defaults = {
        "generator_report": None,
        "source_context": None,
        "audit_metrics": None,
        "job_running": False
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

def _process_pending_jobs() -> None:
    """
    Executes queded background tasks 
    then refreshes the app
    """

    if not st.session_state.job_running:
        return
    
    if "pending_generation" in st.session_state:
        args = st.session_state.pop("pending_generation")
        send_generation_request(**args)
        st.session_state.job_running = False
        st.rerun()
        return
    
    if "pending_audit" in st.session_state:
        args = st.session_state.pop("pending_audit")
        report = st.session_state.generator_report or {}

        send_audit_request(
            answers=report.get("extracted_answers", {}),
            **args
        )
        st.session_state.job_running = False
        st.rerun()
        return
    
def main() -> None:
    """
    Main control flow
    """

    st.set_page_config(page_title="ESM Data Automation", layout="wide")
    st.title("ESM Data Automation")
    st.markdown("Automatically answer templates w/ uploaded info + check for accuracy using AI")

    _initialize_session_state()
    _process_pending_jobs()

    st.sidebar.header("Settings")

    chosen_engine = st.sidebar.selectbox(
        "Select AI Model",
        list(MODEL_CONFIGURATIONS.keys()),
        disabled=st.session_state.job_running,
    )
    target_document = st.sidebar.selectbox(
        "Chose a form template to fill out",
        fetch_server_templates(),
        disabled=st.session_state.job_running,
    )
    judge_iterations = st.sidebar.slider(
        "How many times should the judge test?",
        min_value=2,
        max_value=10,
        value=3,
        disabled=st.session_state.job_running,
    )

    st.header(f"1. Generate {target_document}")

    uploaded_files = st.file_uploader(
        "Drop you scientific data, READMEs, publications, ect... here:",
        accept_multiple_files=True,
        disabled=st.session_state.job_running,
    )
    custom_name = st.text_input(
        "Label this extraction run (optional):",
        placeholder="Project #1",
        disabled=st.session_state.job_running,
    )

    if st.button(
        "Read Files & Write Answers",
        type="primary",
        disabled=not uploaded_files or st.session_state.job_running,
    ):
        st.session_state.job_running = True
        st.session_state.pending_generation = {
            "target_document": target_document,
            "chosen_engine": chosen_engine,
            "uploaded_files": uploaded_files,
            "custom_name": custom_name
        }
        st.rerun()

    if not st.session_state.generator_report:
        return
    
    render_answers_and_missing_sections()

    st.markdown("---")
    st.header("2. LLM Judge")
    st.markdown(f"Run the judge test to quantify the accuracy of {target_document}")

    if st.button("Run Stability Test", disabled=st.session_state.job_running):
        st.session_state.job_running = True
        st.session_state.pending_audit = {
            "chosen_engine": chosen_engine,
            "judge_iterations": judge_iterations,
        }
        st.rerun()
    
    if not st.session_state.audit_metrics:
        return
    
    st.markdown("---")
    st.success("Audit complte!")

    metadata = st.session_state.audit_metrics.get("metadata", {})
    kappa_score = metadata.get("global_gwets_ac1", 0.0)

    st.metric("Agreement score (Gwet's AC1)", kappa_score)
    st.dataframe(
        st.session_state.audit_metrics.get("item_level_stability_metrics", []),
        width="stretch",
    )

if __name__ == "__main__":
    main()

