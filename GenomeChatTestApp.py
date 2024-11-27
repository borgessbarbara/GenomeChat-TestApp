import streamlit as st
from langchain_ollama import OllamaLLM
import os
import gffutils
import io
import sys
import traceback
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional
import time
import threading
import shutil
from PIL import Image

# Constants
STORAGE_DIR = "tempgenomechat"
TEMP_DIR = os.path.join(STORAGE_DIR, "temp")
DB_DIR = os.path.join(STORAGE_DIR, "db")
FILE_EXPIRY_SECONDS = 86400  # 1 day

# Ensure directories exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# Verify Secrets Loading
if "hidden_prompt" not in st.secrets:
    st.error("Hidden prompt not found in secrets. Please check your secrets configuration.")
    st.stop()

# Debug Mode Toggle
debug_mode = st.sidebar.checkbox("Debug Mode")

# Load and display logo
logo = Image.open("logo.png")
col1, col2 = st.columns([10, 7])
with col1:
    st.image(logo, use_container_width=True, width=500)

st.write("Welcome to GenomeChat! Talk to your annotation GTF or GFF file.")

# Load the Gemma 2 9B model
@st.cache_resource
def load_model():
    try:
        return OllamaLLM(model="qwen2.5:7b", temperature=0.2, verbose=True)
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None

model = load_model()
if model is None:
    st.stop()

# Function to delete file after a specified time
def delete_file_after(file_path, delay_seconds):
    def delete_file():
        time.sleep(delay_seconds)
        if os.path.exists(file_path):
            os.remove(file_path)
            if debug_mode:
                st.sidebar.write(f"Debug: Temporary file '{file_path}' deleted after {delay_seconds} seconds.")
    
    thread = threading.Thread(target=delete_file)
    thread.start()

# Convert GTF/GFF to .db
def convert_to_db(uploaded_file):
    try:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in ['.gtf', '.gff', '.gff3']:
            raise ValueError("Unsupported file type. Please upload a GTF, GFF, or GFF3 file.")

        temp_file_path = os.path.join(TEMP_DIR, uploaded_file.name)
        db_filename = os.path.join(DB_DIR, f"{uploaded_file.name}.db")

        # Save the uploaded file
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(uploaded_file.getvalue())

        # Schedule file deletion
        delete_file_after(temp_file_path, FILE_EXPIRY_SECONDS)

        db = gffutils.create_db(temp_file_path, dbfn=db_filename, keep_order=True, force=True, 
                                merge_strategy="create_unique",
                                disable_infer_genes=True,
                                disable_infer_transcripts=True)
        db = gffutils.FeatureDB(db_filename)

        if debug_mode:
            st.sidebar.write(f"Debug: File '{uploaded_file.name}' converted to database and saved temporarily.")
        return db
    except Exception as e:
        st.error(f"Error converting file to database: {str(e)}")
        return None

# Process Queries
def process_query(db, question):
    try:
        if model is None:
            raise ValueError("Model is not initialized")
        
        code_prompt = st.secrets["hidden_prompt"] + f"\nDatabase: {db}\nQuestion: {question}"
        generated_code = model.generate([code_prompt]).generations[0][0].text.strip()
        execution_result = execute_code(generated_code)
        
        analysis_prompt = f"""
        Database: {db}
        Question: {question}
        Generated Code:
        {generated_code}
        Execution result:
        {execution_result}

        Provide a concise and explained answer to the question based on the question and execution results.
        """
        
        analysis_response = model.generate([analysis_prompt])
        return generated_code, execution_result, analysis_response.generations[0][0].text.strip()
    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        return None, None, None

# Execute Code
def execute_code(code):
    code = code.strip("```python").strip().strip("```").strip()
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    local_namespace = {}
    try:
        exec(code, globals(), local_namespace)
    except Exception as e:
        print(f"Error executing code: {str(e)}")
        traceback.print_exc()
    finally:
        sys.stdout = old_stdout
    return redirected_output.getvalue(), local_namespace

annotation_source = st.radio(
    "Select annotation source:",
    ("Upload custom file", "Use Human annotation (Ensembl release 112)")
)

db = None

if annotation_source == "Upload custom file":
    uploaded_file = st.file_uploader("Upload", type=['gtf', 'gff', 'gff3'])

    if uploaded_file is not None:
        file_size = uploaded_file.size
        max_size = st.get_option("server.maxUploadSize") * 1024 * 1024
        if file_size > max_size:
            st.error(f"Uploaded file exceeds the maximum size limit of {max_size/(1024*1024):.2f} MB")
        else:
            db = convert_to_db(uploaded_file)
else:
    # Use the pre-converted human.db file
    db = gffutils.FeatureDB('human.db')
    st.success("Using Human annotation (Ensembl release 112)")

if db:
    st.success("Database loaded. You can now start asking questions!")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Clear Chat History Button
    if st.button("Clear Chat History"):
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# In the main section where results are displayed:
if prompt := st.chat_input("Type your question"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    generated_code, execution_result, analysis = process_query(db, prompt)

    if generated_code and execution_result and analysis:
        with st.chat_message("GenomeChat"):
            st.markdown("### Generated Code:")
            st.code(generated_code, language="python")
            st.markdown("### Execution Result:")
            
            # Get execution result and local namespace
            output, local_vars = execute_code(generated_code)
            
            # Display execution results based on their type
            if 'df' in local_vars and isinstance(local_vars['df'], pd.DataFrame):
                st.dataframe(local_vars['df'])
            elif 'fig' in local_vars and isinstance(local_vars['fig'], plt.Figure):
                st.pyplot(local_vars['fig'])
            else:
                st.code(output)
            
            st.markdown("### Analysis:")
            st.markdown(analysis)
        
        st.session_state.messages.append({
            "role": "GenomeChat", 
            "content": f"### Generated Code:\n```python\n{generated_code}\n```\n### Execution Result:\n```\n{output}\n```\n### Analysis:\n{analysis}"
        })
    else:
        st.error("Failed to process the query. Please try again.")

    if debug_mode:
        st.sidebar.write("Debug: Current session state:", st.session_state)

if debug_mode:
    st.sidebar.write("Debug: Script execution completed.")

# Cleanup function to remove old files (run periodically or on app startup)
def cleanup_old_files():
    current_time = time.time()
    for dir_path in [TEMP_DIR, DB_DIR]:
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            if os.path.isfile(file_path):
                if current_time - os.path.getmtime(file_path) > FILE_EXPIRY_SECONDS:
                    os.remove(file_path)
                    if debug_mode:
                        st.sidebar.write(f"Debug: Old file '{file_path}' removed during cleanup.")

# Run cleanup on app startup
cleanup_old_files()
