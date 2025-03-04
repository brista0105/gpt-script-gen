import openai
import tkinter as tk
from tkinter import messagebox
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

def on_generate_click():
    """
    Event handler when the 'Generate' button is clicked.
    """
    # Gather inputs from the UI
    title = entry_title.get()
    description = entry_description.get()
    duration = int(entry_duration.get())
    modules = entry_modules.get("1.0", "end-1c").splitlines()

    # Validate and create a CourseDetail object
    try:
        course = CourseDetail(
            title=title,
            description=description,
            duration_minutes=duration,
            modules=modules
        )
        
        # Generate course script using GPT
        script = generate_script_with_gpt(course)

        # Display the generated script
        text_output.delete(1.0, tk.END)
        text_output.insert(tk.END, script)
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate course script: {e}")

# Create the main UI window
root = tk.Tk()
root.title("RIA Compliance Training Script Generator")

# Title input
label_title = tk.Label(root, text="Course Title:")
label_title.grid(row=0, column=0, sticky="e")
entry_title = tk.Entry(root, width=40)
entry_title.grid(row=0, column=1)

# Description input
label_description = tk.Label(root, text="Course Description:")
label_description.grid(row=1, column=0, sticky="e")
entry_description = tk.Entry(root, width=40)
entry_description.grid(row=1, column=1)

# Duration input
label_duration = tk.Label(root, text="Course Duration (minutes):")
label_duration.grid(row=2, column=0, sticky="e")
entry_duration = tk.Entry(root, width=40)
entry_duration.grid(row=2, column=1)

# Modules input
label_modules = tk.Label(root, text="Modules (one per line):")
label_modules.grid(row=3, column=0, sticky="ne")
entry_modules = tk.Text(root, width=40, height=6)
entry_modules.grid(row=3, column=1)

# Generate button
button_generate = tk.Button(root, text="Generate Script", command=on_generate_click)
button_generate.grid(row=4, column=1, pady=10)

# Output area
label_output = tk.Label(root, text="Generated Script:")
label_output.grid(row=5, column=0, sticky="ne")
text_output = tk.Text(root, width=50, height=15)
text_output.grid(row=5, column=1)

# Run the main loop to display the UI
root.mainloop()
