import openai
import streamlit as st
import pdfplumber
import docx
from io import BytesIO
from pydantic import BaseModel
from typing import List
import re
from streamlit_quill import st_quill  # Rich text editor for formatting
from bs4 import BeautifulSoup  # Helps preserve HTML-based formatting

# Streamlit UI
st.title("AI Compliance Training Script Generator")

# User Input for OpenAI API Key
st.subheader("OpenAI API Key")
openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password", placeholder="sk-...", key="api_key")

if not openai_api_key:
    st.warning("Please enter your OpenAI API key to generate scripts.")
    st.stop()

openai.api_key = openai_api_key

# File Upload Section
st.subheader("Upload Course Outline (PDF, DOCX)")
uploaded_files = st.file_uploader("Upload multiple course outlines", type=["pdf", "docx"], accept_multiple_files=True)

# User-defined module identifier
st.subheader("Module Identifier")
module_identifier = st.text_input("Enter module identifier (e.g., 'Module', 'Section'):", value="Module")

# Function to extract text while preserving styles from DOCX
def extract_text_from_docx(docx_file):
    try:
        doc = docx.Document(docx_file)
        html_content = []
        for para in doc.paragraphs:
            text = para.text
            style = para.style.name

            if "Heading" in style:
                html_content.append(f"<h2>{text}</h2>")
            elif style.startswith("List") or para.text.startswith(("-", "•", "*")):
                html_content.append(f"<li>{text}</li>")
            elif "Bold" in style or "**" in text:
                html_content.append(f"<b>{text}</b>")
            else:
                html_content.append(f"<p>{text}</p>")
        
        return "\n".join(html_content)
    except Exception as e:
        return f"Error extracting text from DOCX: {e}"

# Function to extract formatted text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            formatted_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    formatted_text.append(f"<p>{text.replace('\n', '<br>')}</p>")  # Preserve line breaks
            return "\n".join(formatted_text)
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

# Define Pydantic models
class ModuleDetail(BaseModel):
    title: str
    content: str
    custom_prompt: str  

class CourseDetail(BaseModel):
    title: str
    description: str
    duration_minutes: int
    audience: str
    regulations: str
    modules: List[ModuleDetail]

# Function to extract modules while keeping formatting
def extract_modules_from_text(text, identifier):
    modules = []
    pattern = rf"\b{re.escape(identifier)}\s+\d+[:.-]?"
    module_matches = re.split(pattern, text, flags=re.IGNORECASE)

    if len(module_matches) > 1:
        for idx, section in enumerate(module_matches[1:], start=1):
            lines = section.strip().split("\n")
            module_title = lines[0].strip() if lines else f"{identifier} {idx} (Untitled)"
            module_content = "\n".join(lines[1:]).strip()
            modules.append(ModuleDetail(title=module_title, content=module_content, custom_prompt=""))
    return modules

# Extract content from uploaded documents
course_modules = []
extracted_texts = {}

if uploaded_files:
    for file in uploaded_files:
        file_type = file.name.split(".")[-1]
        extracted_text = extract_text_from_pdf(file) if file_type == "pdf" else extract_text_from_docx(file) if file_type == "docx" else file.read().decode("utf-8")

        if not extracted_text.strip():
            st.error(f"Could not extract text from {file.name}. Please check the file format.")
            continue

        extracted_texts[file.name] = extracted_text  # Store for Quill Editor

        # Display extracted text with Quill Editor
        extracted_texts[file.name] = st_quill(value=extracted_text, key=f"extracted_{file.name}")

        detected_modules = extract_modules_from_text(extracted_text, module_identifier)
        if detected_modules:
            course_modules.extend(detected_modules)
        else:
            st.warning(f"No modules detected in {file.name} using '{module_identifier}'.")

# Course Metadata Inputs
st.subheader("Course Metadata")
title = st.text_input("Course Title:", placeholder="e.g., 2025 Compliance Essentials for RIAs – Annual Training")
description = st.text_area("Course Description:", placeholder="Provide a brief course summary.")
duration = st.number_input("Course Duration (minutes):", min_value=1, step=1, value=30)
audience = st.selectbox("Intended Audience:", ["RIA Employees", "Compliance Officers", "Investment Advisers", "General Finance Professionals"])
regulations = st.selectbox("Regulatory Alignment:", ["SEC", "FINRA", "Investment Advisers Act of 1940", "Multiple"])

# Function to generate module script
def generate_module_script(module: ModuleDetail, module_number: int) -> str:
    try:
        base_prompt = f"""
        Expand {module_identifier} {module_number} on "{module.title}" in compliance training.
        The module should be 700-1,000 words and include:

        **Learning Objectives:**
        - Define the compliance issue.
        - Provide practical applications.

        **Content:**
        - Overview of the compliance issue.
        - Key regulatory requirements and best practices.
        - Case study illustrating real-world application.

        **Scenario-Based Learning Activity:**
        - Provide a scenario related to "{module.title}".

        **Regulatory References:**
        - Cite SEC, FINRA, or applicable regulations.

        {module.content}
        """
        
        prompt = module.custom_prompt if module.custom_prompt else base_prompt

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an expert in compliance training script generation."},
                      {"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.2
        )

        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Error generating {module_identifier} {module_number}: {e}"

# Generate Script Button
if st.button("Generate Training Script"):
    if not title or not description or not audience or not regulations or not course_modules:
        st.warning("Please fill in all fields before generating the script!")
    else:
        full_script = ""
        for idx, module in enumerate(course_modules, start=1):
            with st.spinner(f"Generating {module_identifier} {idx}: {module.title}..."):
                module_script = generate_module_script(module, idx)
                full_script += module_script + "\n\n"

        # Display final script with Quill Editor
        st.subheader("Final Script with Editing")
        final_script = st_quill(value=full_script, key="final_script")

