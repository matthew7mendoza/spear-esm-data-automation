"""
Handles historical states and user settings sidebar rendering
"""

import logging

import requests
import streamlit as st

from frontend.config import BACKEND_URL

__all__ = ["render_historical_sidebar"]

logger = logging.getLogger(__name__)

def _on_history_change() -> None:
    """
    Intercepts runtime select events to prevent UI
    from getting messy
    """

    selected_job_name = st.session_state.history_selectbox
    if not selected_job_name or selected_job_name == "-- Select Past Run --":
        return
    
    chosen_job = st.session_state.get("task_mapping", {}).get(selected_job_name)
    if not chosen_job:
        return
    
    task_id = chosen_job.get("task_id")
    if not task_id:
        return
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/tasks/{task_id}", timeout=5)
    except requests.exceptions.RequestException as network_transport_fault:
        logger.error("Network communication loss when trying to read historical entries.", exc_info=True)
        st.error(f"Network error trying to fetch historical file profile: {network_transport_fault}")
        return
    
    if response.status_code != 200:
        st.error("Failed to extract full analysis data from backend")
        return
    
    full_job_payload = response.json()
    st.session_state.audit_metrics = None
    st.session_state.generator_report = full_job_payload.get("report")
    st.session_state.source_context = full_job_payload.get("source_context")

def render_historical_sidebar() -> None:
    """
    fetches the history of completed tasks and displays
    them on the sidebar dropdown so users can scroll through past runs
    """

    try:
        response = requests.get(f"{BACKEND_URL}/api/tasks", timeout=5)
    except requests.exceptions.RequestException as connection_offline_error:
        logger.warning(f"Unable to read connection tracking indexes: {connection_offline_error}")
        st.sidebar.caption("History tracker offline!")
        return
    
    if response.status_code != 200:
        st.sidebar.caption("History tracker offline!")
        return
    
    past_tasks = response.json()
    completed_tasks = [
        task for task in past_tasks if task.get("status") == "COMPLETED"
    ]

    if not completed_tasks:
        st.sidebar.caption("No history")
        return
    
    # maps display name to full task data
    # uses the custom name if avaliable, otherwise defaults to 
    # job [first 8 characters of ID]
    task_options = {
        (
            f"{task.get('custom_name')} ({task['task_id'][:8]})"
            if task.get("custom_name")
            else f"Job {task['task_id'][:8]}"
        ): task
        for task in completed_tasks
    }

    st.session_state.task_mapping = task_options
    options_list = ["-- Select Past Run --", *task_options]

    st.sidebar.selectbox(
        "Reload a past analysis:",
        options=options_list,
        key="history_selectbox",
        on_change=_on_history_change,
        disabled=st.session_state.get("job_running", False),
    )

    
