# ui/styles.py
import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        /* =====================================================
           1. GLOBAL APP BACKGROUND + TEXT
           ===================================================== */
        .stApp {
          background-color: #000000;
          color: #FFFFFF;
        }

        /* Ensure all text inherits white */
        .stApp * {
          color: #FFFFFF;
        }

        /* =====================================================
           2. SIDEBAR (Steps + Progress)
           ===================================================== */
        [data-testid="stSidebar"] {
          background-color: #040273;
        }

        [data-testid="stSidebar"] * {
          color: #FFFFFF;
        }

        /* Sidebar links */
        [data-testid="stSidebar"] a {
          color: #FFFFFF;
          text-decoration: none;
        }

        [data-testid="stSidebar"] a:hover {
          text-decoration: underline;
          opacity: 0.9;
        }

        /* =====================================================
           3. INPUT BOXES (dark grey, white text, blue border)
           ===================================================== */
        textarea,
        input,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="input"] input {
          background-color: #1e1e1e;
          color: #FFFFFF;
          border: 1px solid #ff4b4b
        }

        textarea:focus,
        input:focus,
        [data-baseweb="textarea"] textarea:focus,
        [data-baseweb="input"] input:focus {
          border-color: #ff4b4b;
          box-shadow: 0 0 0 1px #b44cff;
          outline: none;
        }

        /* =====================================================
           4. SLIDER (Critique abstraction level)
           ===================================================== */
        [data-testid="stSlider"] > div {
          color: #FFFFFF;
        }

        /* Slider track (inactive) */
        [data-testid="stSlider"] [role="slider"]::before {
          background-color: #444444;
        }

        /* Slider thumb */
        [data-testid="stSlider"] [role="slider"] {
          color: #b44cff;
        }
        /* =====================================================
          BUTTONS (force readable in light & dark browser mode)
          ===================================================== */

        /* Primary & secondary buttons */
        button[kind],
        .stButton > button {
          background-color: #262730 !important;
          color: #FFFFFF !important;
          border: 1px solid #404040 !important;
        }

        button[kind]:hover,
        .stButton > button:hover {
          background-color: #2f3040 !important;
          color: #FFFFFF !important;
        }

        /* Disabled buttons */
        button:disabled,
        .stButton > button:disabled {
          background-color: #1f2028 !important;
          color: #AAAAAA !important;
          border: 1px solid #333333 !important;
        }

        /* =====================================================
          DROPDOWNS / MULTISELECT (BaseWeb)
          ===================================================== */

        /* Closed select box */
        [data-baseweb="select"] > div {
          background-color: #262730 !important;
          color: #FFFFFF !important;
          border: 1px solid #404040 !important;
        }

        /* Selected values (tags like Systems Thinking) */
        [data-baseweb="tag"] {
          background-color: #262730 !important;
          color: #FFFFFF !important;
        }

        /* Dropdown menu */
        [data-baseweb="popover"] {
          background-color: #262730 !important;
          color: #FFFFFF !important;
        }

        /* Dropdown options */
        [data-baseweb="menu"] {
          background-color: #262730 !important;
        }

        [data-baseweb="option"] {
          color: #FFFFFF !important;
        }

        [data-baseweb="option"]:hover {
          background-color: #2f3040 !important;
        }

        """,
        unsafe_allow_html=True,
    )
