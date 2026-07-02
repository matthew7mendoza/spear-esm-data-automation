"""
Renders targeted metrics and data extraction visualizations cleanly
"""

import streamlit as st

__all__ = ["render_answers_and_missing_sections"]

def render_answers_and_missing_sections() -> None:
    """
    Displays the successfully extracted answers and any 
    missing information side-by-side using two columns
    """

    if not st.session_state.generator_report:
        return
    
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
            st.success("The AI found answers to all questions for this template!!!")
            return
        
        for missing_question in missing:
            st.error(f"- {missing_question}")