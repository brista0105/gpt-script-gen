import openai
import streamlit as st
from pydantic import BaseModel
from typing import List

# Set up OpenAI API key
openai.api_key = "your-openai-api-key-here"

# Pydantic model for validating course details
class CourseDetail(BaseModel):
    title: str
    description: str
    duration_minutes: int
    modules: List[str]

def generate_script_with_gpt(course: CourseDetail) -> str:
    """
    Uses GPT to generate a detailed compliance training course script.

    Args:
        course: The course details containing title, description, and modules.

    Returns:
        A generated course script string in the expanded outline format.
    """
    try:
        # Prepare the prompt for GPT
        prompt = (
            f"Generate an expanded outline for a compliance training course for RIAs. "
            f"The course title is '{course.title}' with the following modules:\n"
            f"{', '.join(course.modules)}\n"
            f"The outline should include: Introduction, module breakdown, learning objectives, key content, and references. "
            f"Ensure the format is clear, easy to follow, and includes learning objectives and references."
        )

        # Call GPT API to generate the content
        response = openai.Completion.create(
            engine="text-davinci-003",  # GPT model
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7
        )

        # Return the generated script
        return response.choices[0].text.strip()
    
    except Exception as e:
        print(f"Error generating script: {e}")
        return "An error occurred while generating the script."

# Streamlit UI
st.title("RIA Compliance Training Script Generator")

# Course title input
title = st.text_input("Course Title:")

# Course description input
description = st.text_area("Course Description:")

# Duration input
duration = st.number_input("Course Duration (minutes):", min_value=1, step=1)

# Modules input
modules = st.text_area("Modules (one per line):", height=150)

# Generate script button
if st.button("Generate Script"):
    try:
        # Parse modules
        modules_list = modules.splitlines()
        st.write("Modules List:", modules_list)

        # Validate and create a CourseDetail object
        course = CourseDetail(
            title=title,
            description=description,
            duration_minutes=duration,
            modules=modules_list
        )
        st.write("Course Detail:", course)

        # Generate course script using GPT
        script = generate_script_with_gpt(course)
        st.write("Generated Script:", script)

        # Display the generated script
        st.subheader("Generated Course Script")
        st.text_area("Expanded Outline", script, height=600)

    except Exception as e:
        st.error(f"Failed to generate course script: {e}")