import openai
import streamlit as st
from pydantic import BaseModel
from typing import List

# Streamlit UI
st.title("AI Compliance Training Script Generator")

# User Input for OpenAI API Key
st.subheader("OpenAI API Key")
openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password", placeholder="sk-...", key="api_key")

# Ensure API key is entered before proceeding
if not openai_api_key:
    st.warning("Please enter your OpenAI API key to generate scripts.")
    st.stop()

# Set OpenAI API Key
openai.api_key = openai_api_key

# Define Pydantic model for course details validation
class ModuleDetail(BaseModel):
    title: str

class CourseDetail(BaseModel):
    title: str
    description: str
    duration_minutes: int
    audience: str
    regulations: str
    modules: List[ModuleDetail]

def generate_module_script(module: ModuleDetail, module_number: int) -> str:
    """
    Generates a structured compliance training module script using GPT-4.

    Args:
        module: Module details including title.
        module_number: The module number (e.g., 1, 2, 3).

    Returns:
        A formatted compliance training module as a string.
    """
    try:
        prompt = f"""
        Expand Module {module_number} of a compliance training course on "{module.title}".  
        The module should be 700-1,000 words and include:  
        - A clear definition of the compliance issue.  
        - A practical example or real-world case study relevant to "{module.title}".  
        - A scenario-based learning activity that engages learners in decision-making.  
        - A summary of best practices and regulatory requirements, referencing SEC rules or relevant laws.  
        - Learning Objectives: Include at least two key takeaways learners should gain from this module.  
        - Regulatory References: Cite specific SEC or FINRA regulations where applicable.  
        - Format the output as a structured training module.  
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an expert in compliance training content generation."},
                      {"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7
        )

        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Error generating module {module_number}: {e}"

# Course Title
title = st.text_input("Course Title:", placeholder="e.g., 2025 Compliance Essentials for RIAs – Annual Training")

# Course Description
description = st.text_area("Course Description:", placeholder="Provide a brief description of the course objectives and target audience.")

# Course Duration
duration = st.number_input("Course Duration (minutes):", min_value=1, step=1, value=30)

# Intended Audience
audience = st.selectbox("Intended Audience:", ["RIA Employees", "Compliance Officers", "Investment Advisers", "General Finance Professionals"])

# Regulatory Alignment
regulations = st.selectbox("Regulatory Alignment:", ["SEC", "FINRA", "Investment Advisers Act of 1940", "Multiple"])

# Module Management
st.subheader("Course Modules")
module_count = st.number_input("Number of Modules:", min_value=1, max_value=10, step=1, value=3)

modules = []
for i in range(module_count):
    module_title = st.text_input(f"Module {i+1} Title:", placeholder="e.g., RIA Compliance Basics", key=f"module_title_{i}")
    modules.append(ModuleDetail(title=module_title))

# Generate Script Button
if st.button("Generate Training Script"):
    if not title or not description or not audience or not regulations or any(not mod.title for mod in modules):
        st.warning("Please fill in all fields before generating the script!")
    else:
        try:
            course = CourseDetail(
                title=title,
                description=description,
                duration_minutes=duration,
                audience=audience,
                regulations=regulations,
                modules=modules
            )

            st.subheader("Generated Compliance Training Script")
            
            # Generate content for each module
            full_script = ""
            for idx, module in enumerate(course.modules, start=1):
                with st.spinner(f"Generating Module {idx}: {module.title}..."):
                    module_script = generate_module_script(module, idx)
                    full_script += module_script + "\n\n"
                    st.markdown(module_script, unsafe_allow_html=True)

            # Provide option to download script as a text file
            st.download_button(label="Download Full Script", data=full_script, file_name="compliance_training_script.txt", mime="text/plain")

        except Exception as e:
            st.error(f"Failed to generate script: {e}")
