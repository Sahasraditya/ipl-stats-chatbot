import os
import streamlit as st
from cricgpt_1 import cricgpt 

# Set the OpenAI API Key from the backend (e.g., an environment variable)
# Ensure your API key is securely stored in your backend or environment variables
#os.environ["OPENAI_API_KEY"] 
openai_api_key = os.getenv("OPENAI_API_KEY")  # Make sure the key is stored as an environment variable


# Check if the API key is set
if not openai_api_key:
    st.error("API key not found. Please set the OpenAI API key in the backend.")
else:
    # Streamlit UI components
    st.title('🏏🔗 Cric GPT')
    st.subheader('Updated till IPL 2022')

    st.subheader("📋 Sample Questions")
    sample_questions = [
        "Who scored the most runs in 2018 season?",
        "Which bowler took the most wickets in IPL 2020?",
        "Give me the matchup between Kohli and Bumrah",
        "Who has the best economy rate in the powerplay since 2016? Minimum 100 balls"
    ]

    selected_question = st.radio("Click to select a question:", sample_questions)

    with st.form('my_form'):
        if selected_question:
            st.text_area('Enter text:', value=selected_question, key="question_area")
        else:
            st.text_area('Enter text:', '', key="question_area")
        
        submitted = st.form_submit_button('Submit')
        if submitted:
            result = cricgpt(st.session_state.question_area)
            st.info(result)
