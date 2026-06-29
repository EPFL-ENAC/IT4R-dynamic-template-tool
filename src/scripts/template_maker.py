from git import *
from config import get_vars
import os
import json
import openai
import subprocess

config = get_vars()

client = openai.OpenAI(
    base_url=config["llm_url"],
    api_key=config["llm_key"]
)

# Tool definitions (sent to the LLM)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, creating it if it doesn't exist",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path, '.' for root"}
                },
                "required": ["path"]
            }
        }
    }
]

def make_template_repo(data):

    # Clone the template repository with options provided by the user
    
    clone_options = []
    if data["GitHub"]["include_submodules"]:
        clone_options.append("--recurse-submodules")
    clone_options.append("--branch")
    clone_options.append(data['GitHub']['branch'])
    clone_options.append(data['GitHub']['template_repo'])
    clone_options.append(".")
    subprocess.run(["git", "clone"] + clone_options, check=True)

    # Delete the .git directory to remove the template repository's history
    subprocess.run(["rm", "-rf", ".git"], check=True)

    # Initialize a new git repository in the current directory
    subprocess.run(["git", "init"], check=True)

    # Add new remote origin pointing to the new repository link provided by the user
    subprocess.run(["git", "remote", "add", "origin", data['GitHub']['new_repo_link']], check=True)

    ## LLM Prompt

    base_prompt = "Your role is to convert the current git repository into a template for a new project. You will be provided with the following information about the new project:\n\n"
    base_prompt += '''
    "GitHub": {
        "template_repo": "git@github.com:EPFL-ENAC/template-repo.git", # link to the template repository to clone
        "branch": "main", # branch to clone from the template repository
        "include_submodules": False, # whether to include submodules when cloning the template repository
        "new_repo_link": "git@github.com:EPFL-ENAC/new-repo.git", # link to the new repository to set as the remote origin
    },
    "Projet": {
        "Lab_name": "My Lab", # name of the lab or organization the project belongs to
        "project_name": "My Project", # name of the new project
        "project_description": "A description of my project.", # description of the new project
        "Domain_name_dev": "Development.epfl.ch", # domain name for the development environment
        "Domain_name_prod": "Production.epfl.ch", # domain name for the production environment
        "Domain_name_stage": "Staging.epfl.ch", # domain name for the staging environment
    },
    "CI/CD": {
        "keep_ci": True, # whether to keep the existing CI/CD configuration from the template repository
        "keep_pre_commits": True, # whether to keep the existing pre-commit configuration from the template repository
    },
    "Updates": {
        "dependances": True, # whether to update the dependencies in the template repository to the latest versions
        "pre-commit": True, # whether to update the pre-commit configuration in the template repository to the latest versions
        "ci_cd": True, # whether to update the CI/CD configuration in the template repository to the latest versions
    },
    "LLM": {
        "additional_prompt": "" # any additional instructions or information to provide to the you when generating the template
    }'''
    
    base_prompt += "\nYour task is to identify all code / information that is specific to the old project and replace it with data provided in the new project information. You should also replace any old project specific information with placeholders in the format {{SECTION_KEY}}. For example, if the old project name is 'OldProject' and the new project name is 'NewProject', you should replace all instances of 'OldProject' in the code with '{{PROJET_project_name}}'.\n\nPlease provide a list of all placeholders you have created and the corresponding values from the new project information."
    base_prompt += "\n\nHere is the current state of the repository:\n\n"
    
    # use tree command to get the file structure of the repository
    tree_output = subprocess.check_output(["tree", "-a", "-I", "node_modules|.git"], text=True)
    base_prompt += tree_output

    base_prompt += "Here is the configuration for the new project:\n\n"
    for section, values in data.items():
        base_prompt += f"{section}:\n"
        for key, value in values.items():
            base_prompt += f"  - {key}: {value}\n"

    with open("llm_prompt.txt", "w") as f:
        f.write(base_prompt)

    
    return


# --- Tool implementations ---

def read_file(path: str, root: str) -> str:
    full_path = os.path.join(root, path)
    with open(full_path, "r") as f:
        return f.read()

def write_file(path: str, content: str, root: str) -> str:
    full_path = os.path.join(root, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    return f"Written: {path}"

def list_directory(path: str, root: str) -> str:
    full_path = os.path.join(root, path)
    entries = os.listdir(full_path)
    return json.dumps(entries)

def dispatch_tool(name: str, args: dict, root: str) -> str:
    if name == "read_file":
        return read_file(args["path"], root)
    elif name == "write_file":
        return write_file(args["path"], args["content"], root)
    elif name == "list_directory":
        return list_directory(args["path"], root)
    else:
        return f"Unknown tool: {name}"

# --- Agentic loop ---
def run_llm_agent(prompt: str, project_root: str, model: str = "Qwen/Qwen3.5-122B-A10B"):
    messages = [{"role": "user", "content": prompt}]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message)  # keep the assistant turn in history

        # No tool calls → LLM is done
        if not message.tool_calls:
            print("Agent finished:", message.content)
            break

        # Execute each tool call and feed results back
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"  → {name}({args})")

            result = dispatch_tool(name, args, project_root)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })