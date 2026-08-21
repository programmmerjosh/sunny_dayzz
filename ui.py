import streamlit as st


def apply_theme():
    st.markdown(
        """
        <style>
        .block-container {max-width: 1240px; padding-top: 2.2rem; padding-bottom: 3rem;}
        [data-testid="stMetric"] {
            background: color-mix(in srgb, var(--background-color) 92%, #f2b84b 8%);
            border: 1px solid color-mix(in srgb, var(--text-color) 14%, transparent);
            border-radius: 14px;
            padding: 1rem 1.1rem;
        }
        [data-testid="stMetricValue"] {font-size: 2rem;}
        h1, h2, h3 {letter-spacing: -0.025em;}
        hr {margin: 1.4rem 0;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message="No usable forecast data is available for this selection."):
    st.info(message)
    st.stop()
