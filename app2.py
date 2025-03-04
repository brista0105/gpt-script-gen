import openai
import streamlit as st
import pdfplumber
import docx  # Corrected import
from pydantic import BaseModel
from typing import List
import re  # Import regex for module extraction

# Streamlit UI
st.title("AI Compliance Training Script Generator")

# User Input for OpenAI API Key
st.subheader("OpenAI API Key")
openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password", placeholder="sk-...", key="api_key")

if not openai_api_key:
    st.warning("Please enter your OpenAI API key to generate scripts.")
    st.stop()

# Set OpenAI API Key
openai.api_key = openai_api_key

# File Upload Section
st.subheader("Upload Course Outline (PDF, DOCX, TXT)")
uploaded_files = st.file_uploader("Upload one or multiple course outlines", type=["pdf", "docx", "txt"], accept_multiple_files=True)

# User-defined module identifier
st.subheader("Module Identifier")
module_identifier = st.text_input("Enter your module identifier (e.g., 'Module', 'Section', 'Topic'):", value="Module")

# Function to extract text from a DOCX file
def extract_text_from_docx(docx_file):
    try:
        doc = docx.Document(docx_file)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        return f"Error extracting text from DOCX: {e}"

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

# Define Pydantic model for validation
class ModuleDetail(BaseModel):
    title: str
    content: str  # Extracted structured content

class CourseDetail(BaseModel):
    title: str
    description: str
    duration_minutes: int
    audience: str
    regulations: str
    modules: List[ModuleDetail]

# Function to extract modules from text based on user-defined identifier
def extract_modules_from_text(text, identifier):
    modules = []
    
    # Build regex pattern dynamically based on user input (case-insensitive)
    pattern = rf"\b{re.escape(identifier)}\s+\d+[:.-]?"

    module_matches = re.split(pattern, text, flags=re.IGNORECASE)  # Case-insensitive

    if len(module_matches) > 1:  # Found multiple sections
        for idx, section in enumerate(module_matches[1:], start=1):  # Skip the first split (before Module 1)
            lines = section.strip().split("\n")
            module_title = lines[0].strip() if lines else f"{identifier} {idx} (Untitled)"
            module_content = "\n".join(lines[1:]).strip()
            modules.append(ModuleDetail(title=module_title, content=module_content))

    return modules

# Extract content from uploaded documents
course_modules = []
if uploaded_files:
    for file in uploaded_files:
        file_type = file.name.split(".")[-1]
        
        if file_type == "pdf":
            extracted_text = extract_text_from_pdf(file)
        elif file_type == "docx":
            extracted_text = extract_text_from_docx(file)
        else:
            extracted_text = file.read().decode("utf-8")

        if not extracted_text.strip():
            st.error(f"Could not extract text from {file.name}. Please check the file format.")
            continue

        st.text_area(f"Extracted Course Outline from {file.name}", extracted_text, height=300)
        
        # Detect modules using the user-defined identifier
        detected_modules = extract_modules_from_text(extracted_text, module_identifier)

        if detected_modules:
            course_modules.extend(detected_modules)
        else:
            st.warning(f"No modules detected in {file.name} using '{module_identifier}'. Try a different identifier.")

# Course Metadata Input Fields
st.subheader("Course Metadata")
title = st.text_input("Course Title:", placeholder="e.g., 2025 Compliance Essentials for RIAs – Annual Training")
description = st.text_area("Course Description:", placeholder="Provide a brief description of the course objectives and target audience.")
duration = st.number_input("Course Duration (minutes):", min_value=1, step=1, value=30)
audience = st.selectbox("Intended Audience:", ["RIA Employees", "Compliance Officers", "Investment Advisers", "General Finance Professionals"])
regulations = st.selectbox("Regulatory Alignment:", ["SEC", "FINRA", "Investment Advisers Act of 1940", "Multiple"])

# Function to generate a module script based on the structured outline
def generate_module_script(module: ModuleDetail, module_number: int) -> str:
    try:
        prompt = f"""
        Expand {module_identifier} {module_number} of a compliance training course on "{module.title}".  
        The module should be 700-1,000 words and include:  
        - A clear definition of the compliance issue.  
        - A practical example or real-world case study relevant to "{module.title}".  
        - A scenario-based learning activity that engages learners in decision-making.  
        - A summary of best practices and regulatory requirements, referencing SEC rules or relevant laws.  
        - Learning Objectives: Include at least two key takeaways learners should gain from this module.  
        - Regulatory References: Cite specific SEC or FINRA regulations where applicable.  
        - Format the output as a structured training module based strictly on this content:  

        {module.content}
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an expert in compliance training content generation."},
                      {"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3  # Lower temperature for strict adherence
        )

        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Error generating {module_identifier} {module_number}: {e}"

# Generate Script Button
if st.button("Generate Training Script"):
    if not title or not description or not audience or not regulations or not course_modules:
        st.warning("Please fill in all fields before generating the script!")
    else:
        try:
            course = CourseDetail(
                title=title,
                description=description,
                duration_minutes=duration,
                audience=audience,
                regulations=regulations,
                modules=course_modules
            )

            st.subheader("Generated Compliance Training Script")
            
            # Generate content for each module
            full_script = ""
            for idx, module in enumerate(course.modules, start=1):
                with st.spinner(f"Generating {module_identifier} {idx}: {module.title}..."):
                    module_script = generate_module_script(module, idx)
                    full_script += module_script + "\n\n"
                    st.markdown(module_script, unsafe_allow_html=True)

            # Provide option to edit script
            edited_script = st.text_area("Edit Your Script Before Exporting", full_script, height=400)

            # Provide option to download script as a text file
            st.download_button("Download Full Script", data=edited_script, file_name="compliance_training_script.txt", mime="text/plain")

        except Exception as e:
            st.error(f"Failed to generate script: {e}")
