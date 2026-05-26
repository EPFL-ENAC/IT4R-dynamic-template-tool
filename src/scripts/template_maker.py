from git import *
from config import get_vars
from git import Repo
import os

def make_template_repo(data):
    config = get_vars()

    # Clone the template repository with options provided by the user
    
    clone_options = ""
    if data["GitHub"]["include_submodules"]:
        clone_options += "--recurse-submodules "
    clone_options += f"--branch {data['GitHub']['branch']} "
    clone_options += f"{data['GitHub']['template_repo']} "
    clone_options += f" -key"
    os.system(f"git clone {clone_options}")

    # Delete the .git directory to remove the template repository's history
    os.system("rm -rf .git")

    # Initialize a new git repository in the current directory
    os.system("git init")

    # Add new remote origin pointing to the new repository link provided by the user
    os.system(f"git remote add origin {data['GitHub']['new_repo_link']}")

    ## LLM Prompt

    base_prompt = "Your role is to convert the current git repository into a template for a new project. You will be provided with the following information about the new project:\n\n"
    for section, values in data.items():
        base_prompt += f"{section}:\n"
        for key, value in values.items():
            base_prompt += f"  - {key}: {value}\n"
    base_prompt += "\nYour task is to identify all code / information that is specific to the old project and replace it with data provided in the new project information. You should also replace any old project specific information with placeholders in the format {{SECTION_KEY}}. For example, if the old project name is 'OldProject' and the new project name is 'NewProject', you should replace all instances of 'OldProject' in the code with '{{PROJET_project_name}}'.\n\nPlease provide a list of all placeholders you have created and the corresponding values from the new project information."
    base_prompt += "\n\nHere is the current state of the repository:\n\n"
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith((".py", ".md", ".txt", ".json", ".yaml", ".yml")):  # Only include certain file types
                with open(os.path.join(root, file), "r") as f:
                    content = f.read()
                    base_prompt += f"File: {os.path.join(root, file)}\n"
                    base_prompt += content + "\n\n"
    base_prompt += "Please provide the modified files with placeholders and the list of placeholders created."
    base_prompt += "Here is the configuration for the new project:\n\n"
    for section, values in data.items():
        base_prompt += f"{section}:\n"
        for key, value in values.items():
            base_prompt += f"  - {key}: {value}\n"
    os.write("llm_prompt.txt", base_prompt)

    