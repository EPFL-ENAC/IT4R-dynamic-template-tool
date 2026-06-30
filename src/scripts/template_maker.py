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

MAX_AGENT_TURNS = 30  # safety cap so a confused model can't loop forever / burn quota

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

    # --- Safety net: commit a clean baseline before the LLM touches anything.
    # This gives you a diffable, revertable snapshot ("git diff", "git checkout -- .")
    # in case the agent makes a bad edit.
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: baseline snapshot before LLM templating pass"],
        check=True
    )

    # --- Scripted structural changes (keep_backend / keep_frontend) ---
    # These are deterministic enough to not need the LLM, so handle them here,
    # before the agent ever sees the tree. That also means the LLM's prompt/tree
    # reflects the *post-removal* state, which keeps it from wasting time on
    # files that are about to disappear anyway.
    project_cfg = data.get("Projet", {})
    keep_backend = data.get("Architecture", {}).get("keep_backend", True)
    keep_frontend = data.get("Architecture", {}).get("keep_frontend", True)

    if not keep_backend and os.path.isdir("backend"):
        subprocess.run(["rm", "-rf", "backend"], check=True)
    if not keep_frontend and os.path.isdir("frontend"):
        subprocess.run(["rm", "-rf", "frontend"], check=True)

    ## LLM Prompt

    base_prompt = (
        "Your role is to convert the current git repository (a generic template) "
        "into a finished, ready-to-use repository for a brand new project. "
        "You will be given configuration values for the new project below.\n\n"
    )
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
    "Architecture": {
        "keep_backend": True, # whether the backend code was kept (already applied before you start)
        "keep_frontend": True, # whether the frontend code was kept (already applied before you start)
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
        "additional_prompt": "" # any additional instructions or information to provide to you when generating the project
    }'''

    # IMPORTANT: this is a direct substitution task, not a templating task.
    # We are instantiating ONE concrete project from the template, not producing
    # a reusable {{PLACEHOLDER}} template. Do not ask for both in the same pass --
    # if you also want a reusable template artifact later, that is a separate
    # prompt/run with different instructions.
    base_prompt += (
        "\n\nYour task: find every piece of code, text, or configuration that is "
        "specific to the OLD/generic template project, and replace it with the "
        "real values from the 'Projet' (and related) sections above. Examples: "
        "project name, lab name, description, domain names, URLs, any placeholder "
        "strings like 'My Project' or 'My Lab' used as examples in the template. "
        "Do NOT introduce {{PLACEHOLDER}} syntax -- the output should be the final, "
        "concrete repository content for this specific new project, not a reusable "
        "template.\n\n"
        "You must make the changes directly using the tools you have been given:\n"
        "  - Use list_directory to explore folders you have not yet inspected.\n"
        "  - Use read_file to read the current content of any file before editing it.\n"
        "  - Use write_file to save the modified content back to disk.\n"
        "Do not just describe the changes in your response -- actually call the "
        "tools to apply them. Only respond with plain text (no further tool calls) "
        "once every relevant file has been updated, and in that final message give "
        "a short bullet list summarizing what you changed and in which files.\n\n"
        "Also apply, where relevant in code/config/docs:\n"
        "  - CI/CD: if keep_ci is False, remove or neutralize CI pipeline config "
        "files; if keep_pre_commits is False, remove pre-commit config.\n"
        "  - Updates: if dependances is True, you do not need to bump dependency "
        "versions yourself (that is handled separately), just leave dependency "
        "files structurally intact.\n"
        "  - LLM.additional_prompt, if non-empty, contains extra instructions from "
        "the user that take priority over the generic guidance above.\n"
    )

    base_prompt += "\n\nHere is the current state of the repository (after scripted backend/frontend removal):\n\n"

    # use tree command to get the file structure of the repository
    tree_output = subprocess.check_output(["tree", "-a", "-I", "node_modules|.git"], text=True)
    base_prompt += tree_output

    base_prompt += "\nHere is the configuration for the new project:\n\n"
    for section, values in data.items():
        base_prompt += f"{section}:\n"
        for key, value in values.items():
            base_prompt += f"  - {key}: {value}\n"

    with open("llm_prompt.txt", "w") as f:
        f.write(base_prompt)

    # --- Run the agent loop so the LLM actually edits the filesystem ---
    run_llm_agent(base_prompt, project_root=".")

    # --- Commit the LLM's changes as a separate commit, so the baseline
    # commit above stays as a clean rollback point ("git diff HEAD~1" to review).
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"chore: LLM-templated for {project_cfg.get('project_name', 'new project')}"],
        check=True
    )

    return


# --- Tool implementations ---

def _safe_join(root: str, path: str) -> str:
    """Join root + path and reject any attempt to escape root via '..' or an
    absolute path. Defense in depth: the LLM's tool args are not fully trusted
    input even though they come from your own endpoint."""
    full_path = os.path.normpath(os.path.join(root, path))
    root_abs = os.path.abspath(root)
    full_abs = os.path.abspath(full_path)
    if not (full_abs == root_abs or full_abs.startswith(root_abs + os.sep)):
        raise ValueError(f"Path '{path}' escapes project root, refusing")
    return full_path


def read_file(path: str, root: str) -> str:
    full_path = _safe_join(root, path)
    with open(full_path, "r") as f:
        return f.read()


def write_file(path: str, content: str, root: str) -> str:
    full_path = _safe_join(root, path)
    dirname = os.path.dirname(full_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    return f"Written: {path}"


def list_directory(path: str, root: str) -> str:
    full_path = _safe_join(root, path)
    entries = os.listdir(full_path)
    return json.dumps(entries)


def dispatch_tool(name: str, args: dict, root: str) -> str:
    try:
        if name == "read_file":
            return read_file(args["path"], root)
        elif name == "write_file":
            return write_file(args["path"], args["content"], root)
        elif name == "list_directory":
            return list_directory(args["path"], root)
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        # Feed errors back to the model as the tool result instead of crashing
        # the whole run -- the LLM can usually recover (e.g. wrong path, retry).
        return f"ERROR: {e}"


# --- Agentic loop ---
def run_llm_agent(prompt: str, project_root: str, model: str = "Qwen/Qwen3.5-122B-A10B"):
    messages = [{"role": "user", "content": prompt}]

    for turn in range(MAX_AGENT_TURNS):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message)  # keep the assistant turn in history

        # No tool calls -> LLM is done
        if not message.tool_calls:
            print("Agent finished:", message.content)
            return

        # Execute each tool call and feed results back
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"  [{turn}] -> {name}({args})")

            result = dispatch_tool(name, args, project_root)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    print(
        f"WARNING: hit MAX_AGENT_TURNS ({MAX_AGENT_TURNS}) without the agent "
        "signaling completion. Stopping -- review changes manually before "
        "trusting this run."
    )