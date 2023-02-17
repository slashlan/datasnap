### DATASNAP - QUICK EDA EXPLORER APPLICATION ###
# to launch the app on ANACONDA console, activate virtual env and run: streamlit run C:\Users\marco\PycharmProjects\datasnap\app.py
# to generate requirements.txt run this on command prompt console: pipreqs C:\Users\pistis\PycharmProjects\datasnap

# IMPORT LIBRARIES

import pandas as pd
import streamlit as st
from PIL import Image
import json
import requests
from streamlit_chat import message as st_message
from ydata_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report


# APP START
tab1, tab2, tab3 = st.tabs(["Home", "🤖 Conversational Dataset", "📊 Data Profiler"])

with tab1:
    image_title = Image.open('C:/Users/marco/PycharmProjects/datasnap/DataSnap_logo_small.png')
    st.image(image_title, width=600)
    # st.title('')

    # Text
    st.markdown('**Datasnap** is a data exploration tool that allows you to explore your data quickly and efficiently.')
    st.markdown("- **🤖Conversational dataset**: allows you to query the dataset via natural language questions and retrieve"
                " the data you are looking for.")
    st.markdown("- **📊Data profiler**: provides a thorough diagnostic of the dataset and efficient widgets to explore it.")

    st.markdown('''
    <style>
    [data-testid="stMarkdownContainer"] ul{
        list-style-position: inside;
    }
    </style>
    ''', unsafe_allow_html=True)

    # Test session state dummy data
    if 'sample_data' not in st.session_state:
        st.session_state.sample_data = 0

    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx'], key='data_file')

    if uploaded_file is not None:
        if str(uploaded_file.name).endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            # st.write(df.head())
            st.success(
                'File loaded! Go to 🤖 Conversational Dataset to ask questions about your data or to \n📊 Data Profiler to explore your data.',
                icon="✅")
        elif str(uploaded_file.name).endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            # st.write(df.head())
            st.success('File loaded! Go to 🤖 Conversational Dataset to ask questions about your data or to \n📊 Data Profiler to explore your data.', icon="✅")
        else:
            raise Exception("Cannot read this file extension, sorry!")
    else:
        st.markdown(
            "**N.B. Sample data is loaded automatically. You can play with it or load your dataset here above.**")
        df = pd.read_csv('/app/datasnap/Mountains.csv')
        st.session_state.sample_data = True
        st.success('Sample data loaded. Go to 🤖 Conversational Dataset or to \n📊 Data Profiler to test the app.', icon="✅")

with tab2:
    st.header("🤖 Conversational Dataset")
    if uploaded_file is not None or st.session_state.sample_data is True:
        st.sidebar.header("🤖 Chat")
        # Connect to API HF
        API_token = st.secrets["API_TOKEN_HF"]
        headers = {"Authorization": f"Bearer {str(API_token)}"}
        API_URL = "https://api-inference.huggingface.co/models/google/tapas-base-finetuned-wtq"

        # API call
        def query(payload):
            data = json.dumps(payload)
            response = requests.request("POST", API_URL, headers=headers, data=data)
            return json.loads(response.content.decode("utf-8"))


        # Initialize state variables:
        if 'input' not in st.session_state:
            st.session_state.input = ""

        # Start chat & show dataset header
        st.markdown("**Dataset column names:**")
        st.write(", ".join(df.columns))
        st.write(df.head())

        # Define functions

        def generate_response(question, df_dict):
            response = query(
                {
                    "inputs": {
                        "query": question,
                        "table": df_dict,
                    },
                }
            )
            if "cells" in response:
                answer = "Should be " + ', '.join(response["cells"])
                explanation_lbl = "This is what the model did:\n - answer: aggregation method utilized + selected values" \
                                  "\n - coordinates: row, column position of the values retrieved from the dataset"
                explain_resp = {key: response[key] for key in response.keys() & {'answer', 'coordinates'}}
            else:
                raise Exception("I didn't understand your question, can you rephrase?")
            return answer, explain_resp, explanation_lbl


        def get_text():
            input_text = st.text_input('Your question:', key="input")
            return input_text


        # SIDEBAR CHAT
        with st.sidebar:
            if 'generated' not in st.session_state:
                st.session_state['generated'] = []

            if 'past' not in st.session_state:
                st.session_state['past'] = []

            st.markdown(
                'Ask questions like _"What is the mountain with the smallest number of ascents bef. 2004?"_ **:red[Hint:]** Use column names from the dataset in your question to improve accuracy.')

            # Get user input
            user_input = get_text()

            if user_input:
                # Generate ChatTable output
                output, explanation, explanation_label = generate_response(user_input, df.astype('str').to_dict('list'))
                # Store output
                st.session_state.past.append(user_input)
                st.session_state.generated.append(output)

            if st.session_state['generated']:
                for i in range(len(st.session_state['generated']) - 1, -1, -1):
                    st_message(st.session_state["generated"][i], key=str(i))
                    st_message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')

        # MAIN PAGE

        # Show details of query
        st.markdown("**⬇️Dataset filtered according to your question**")

        # Show filtered dataset based on question
        if user_input:
            output, explanation, explanation_label = generate_response(user_input, df.astype('str').to_dict('list'))

            # Show filtered data
            df_row_list = [item[0] for item in explanation["coordinates"][:]]
            # # st.write(df_row_list)
            st.write(df.iloc[df_row_list])
            expander = st.expander("See detailed outcome from model (JSON format)")
            expander.write(explanation_label)
            expander.write(explanation)
        else:
            print("")

with tab3:
    st.subheader("📊 Data Profiler")
    if uploaded_file is not None or st.session_state.sample_data is True:
        # Results from uploaded file
        pr = df.profile_report()
        st_profile_report(pr)
