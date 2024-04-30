from openai import OpenAI
import streamlit as st
import instructor
from files import *
import json

def main():
    
    log_debug_info('[I] Starting Application...')
    st.title("Tribal Resume Converter")

    api_key = ''
    config_path = 'config.json'

    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
            api_key = config.get('api_key', '')

        if not api_key:
            error_message = 'API key not found in the configuration file.'
            log_debug_info(f'[E] {error_message}')
            st.error(error_message)
            st.stop()

        client = OpenAI(api_key=api_key)
        client = instructor.from_openai(client)
        log_debug_info('[I] API key loaded successfully.')

    except FileNotFoundError:
        error_message = 'Configuration file not found.'
        log_debug_info(f'[E] {error_message}')
        st.error(error_message)
        st.stop()

    except json.JSONDecodeError:
        error_message = 'Invalid JSON format in the configuration file.'
        log_debug_info(f'[E] {error_message}')
        st.error(error_message)
        st.stop()

    except Exception as e:
        error_message = f'An error occurred while loading the API key: {str(e)}'
        log_debug_info(f'[E] {error_message}')
        st.error(error_message)
        st.stop()
    
    # Initialize session state for storing processed files
    if 'processed_files_doctors' not in st.session_state:
        st.session_state.processed_files_doctors = []
    if 'processed_files_nurses' not in st.session_state:
        st.session_state.processed_files_nurses = []

    # File uploaders
    uploaded_files_doctors = st.file_uploader("Upload doctors' resumes", accept_multiple_files=True, type=['pdf', 'docx'], key="doctors")
    uploaded_files_nurses = st.file_uploader("Upload nurses' resumes", accept_multiple_files=True, type=['pdf', 'docx'], key="nurses")
    
    # Process files button
    if st.button("Process Files"):
        # Clear previous session data
        st.session_state.processed_files_doctors = []
        st.session_state.processed_files_nurses = []

        file_doctors, file_nurses = process_files(client, uploaded_files_doctors, uploaded_files_nurses)
        
        if file_doctors:
            st.session_state.processed_files_doctors = file_doctors
        if file_nurses:
            st.session_state.processed_files_nurses = file_nurses

    # Display download buttons if there are processed files
    if st.session_state.processed_files_doctors:
        download_processed_files(st.session_state.processed_files_doctors, 'doctors')
    if st.session_state.processed_files_nurses:
        download_processed_files(st.session_state.processed_files_nurses, 'nurses')

if __name__ == "__main__":
    main()