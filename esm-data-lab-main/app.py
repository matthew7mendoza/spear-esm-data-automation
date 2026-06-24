import streamlit as st
from data.gems_data import GEMS_DIRECTORY


def render_header():
    st.title("Gemini Gems Directory")
    st.write("Click on a tab below to get directed to the Gemini Gem")
    st.divider()


def render_gems_directory():


    tab_titles = [f"Tab {index + 1}: {gem['title']}" for index, gem in enumerate(GEMS_DIRECTORY)]
    tabs = st.tabs(tab_titles)

    for current_tab, gem_info in zip(tabs, GEMS_DIRECTORY):

        with current_tab:
            st.subheader(gem_info["title"])
            st.write(gem_info["description"])

            st.link_button(
                label=f"Launch {gem_info['title']}",
                url=gem_info["url"]
            )


def main():

    st.set_page_config(
        page_title="Gemini Gems Directory",
        layout="centered"
    )

    render_header()
    render_gems_directory()

    st.divider()

if __name__ == "__main__":
    main()
