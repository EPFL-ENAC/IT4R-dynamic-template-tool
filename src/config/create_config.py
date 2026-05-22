import json
import os

def create_config(config_path):

    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    new_config = {
        "github_ssh_key": "~/.ssh/id_ed25519",
        "infisical_url": "https://enac-it-secrets.epfl.ch/",
        "infisical_key": "",
        "llm_url": "https://inference-rcp.epfl.ch/v1/",
        "llm_key": "",
    }

    print(f"Creating default config at {config_path}...")

    print("- Please enter the path to your GitHub SSH key for repository access.")
    github_ssh_key = input(f"GitHub SSH Key Path [default: \"{new_config['github_ssh_key']}\"]: ")

    print("- Please enter the URL of your Infisical instance for secret management.")
    infisical_url = input(f"Infisical URL [default: \"{new_config['infisical_url']}\"]: ")

    print("- Please enter your Infisical API key for secret management.")
    infisical_key = input(f"Infisical API Key [default: \"{new_config['infisical_key']}\"]: ")

    print("- Please enter the URL of your LLM provider (e.g., OpenAI, Azure).")
    llm_url = input(f"LLM URL [default: \"{new_config['llm_url']}\"]: ")

    print("- Please enter the API key for your LLM provider.")
    llm_key = input(f"LLM API Key [default: \"{new_config['llm_key']}\"]: ")

    new_config['github_ssh_key'] = github_ssh_key if github_ssh_key != '' else new_config['github_ssh_key']
    new_config['infisical_url'] = infisical_url if infisical_url != '' else new_config['infisical_url']
    new_config['infisical_key'] = infisical_key if infisical_key != '' else new_config['infisical_key']
    new_config['llm_url'] = llm_url if llm_url != '' else new_config['llm_url']
    new_config['llm_key'] = llm_key if llm_key != '' else new_config['llm_key']

    with open(config_path, 'w') as config_file:
        json.dump(new_config, config_file)

    print(f"New config created at {config_path}. Please check it before running the application again.")