import streamlit as st
from datetime import date, timedelta
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from config import collect_cloud_cover_template

# Streamlit UI
st.title("Cloud Cover Data Collector")

# Inputs
api_key = st.text_input("Enter your OpenAI API Key", type="password")
loc = st.text_input("Location")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")

today = date.today()
two_weeks_after_today = today + timedelta(weeks=2)

# we want to limit the user's search to a max of 2 weeks
if end_date > two_weeks_after_today:
    end_date = two_weeks_after_today

# Submit button
if st.button("Submit"):
    if not all([api_key, loc, start_date, end_date]):
        st.warning("Please fill in all the fields above.")
    else:
        # Initialize LLM
        llm = OpenAI(
            openai_api_key=api_key, 
            temperature=0.0,
            max_tokens=3776, 
        )

        # Prompt construction
        prompt = PromptTemplate(
            input_variables=['location', 'start_date', 'end_date', 'todays_date'],
            template=collect_cloud_cover_template
        )

        # Format input dates to strings
        start_date_str = start_date.strftime("%d/%m/%Y")
        end_date_str = end_date.strftime("%d/%m/%Y")
        todays_date_str = end_date.strftime("%d/%m/%Y %H:%M")

        with st.spinner("Fetching data from OpenAI..."):
            response = llm(prompt.format(
                location=loc, 
                start_date=start_date_str, 
                end_date=end_date_str,
                todays_date=todays_date_str
            ))

        # Display response with scroll and copy
        st.subheader("Response")
        with st.container():
            st.markdown(
                """
                <div style='max-height: 300px; overflow-y: auto; padding: 1em; border: 1px solid #ddd; border-radius: 0.5em; background-color: #f8f8f8;'>
                """,
                unsafe_allow_html=True
            )

            st.code(response, language="markdown")

            st.markdown("</div>", unsafe_allow_html=True)
