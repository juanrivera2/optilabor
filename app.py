import os
import cv2
import numpy as np
from PIL import Image
import easyocr
from ultralytics import YOLO
import streamlit as st
import pymssql
from pymongo import MongoClient
import gridfs

# --- Set page configuration ---
st.set_page_config(page_title="PDF Tag Detection", layout="wide")

# --- Database Configuration ---
# MSSQL Database Connection
def connect_to_mssql():
    mssql_server = 'rfocentral02.database.windows.net'
    mssql_database = 'RFOCentral_Dev3' 
    mssql_username = 'AiProjectTestUser'
    mssql_password = '7GJ407c^uOY['
    mssql_table = 'AttachmentXRef'
    return pymssql.connect(server, username, password, database)

# MongoDB Connection
mongo_uri = "mongodb+srv://AIDatabase:BTColombia2022@sandbox.bxohv.mongodb.net/?retryWrites=true&w=majority&appName=sandbox"
mongo_db_name = "AIDatabase"
mongo_collection = "fs.files"

try:
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[mongo_db_name]
    fs = gridfs.GridFS(mongo_db)
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

# --- Main Application ---
reader = easyocr.Reader(['en'], verbose=True)
model_path = "yolov5s.pt"  # Replace with your YOLO model path
model = YOLO(model_path)

st.title("PDF Tag Detection and Database Integration")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file is not None:
    # Save the uploaded file
    save_path = os.path.join("uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"File {uploaded_file.name} uploaded and saved!")

    # --- Save PDF to MongoDB ---
    try:
        with open(save_path, "rb") as pdf_file:
            file_id = fs.put(pdf_file, filename=uploaded_file.name)
        st.success(f"File {uploaded_file.name} successfully uploaded to MongoDB with ID: {file_id}")
    except Exception as e:
        st.error(f"Error saving file to MongoDB: {e}")

    # --- YOLO Detection for Tags ---
    st.subheader("Tag Detection")
    tags = []  # To store detected tags

    # Process the uploaded file (dummy processing for demonstration)
    st.info("Processing file for tag detection...")
    # Add actual YOLO-based tag detection logic here

    # Example dummy tags for demonstration
    tags = ["Tag1", "Tag2", "Tag3"]

    st.write("Detected Tags:", tags)

    # --- Insert into MSSQL Database ---
    try:
        conn = connect_to_mssql()
        cursor = conn.cursor()

        # Insert file name into the database
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM AttachmentsXRef WHERE FileName = %s)
            BEGIN
                INSERT INTO AttachmentsXRef (FileName, TagID) VALUES (%s, '')
            END
        """, (uploaded_file.name, uploaded_file.name))

        # Update TagID column with detected tags
        cursor.execute("""
            UPDATE AttachmentsXRef
            SET TagID = CASE 
                WHEN TagID = '' THEN %s
                ELSE CONCAT(TagID, ',', %s)
            END
            WHERE FileName = %s
        """, (','.join(tags), ','.join(tags), uploaded_file.name))

        conn.commit()
        st.success(f"File and tags successfully updated in MSSQL database!")
    except Exception as e:
        st.error(f"Error updating MSSQL database: {e}")
    finally:
        if conn:
            conn.close()
