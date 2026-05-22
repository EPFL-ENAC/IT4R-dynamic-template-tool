import json

def validate_config(config_path):
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)

        required_fields = ["github_ssh_key", "infisical_url", "infisical_key", "llm_url", "llm_key"]
        for field in required_fields:
            if field not in config or not config[field]:
                print(f"Config validation error: '{field}' is missing or empty.")
                return False

        return True

    except Exception as e:
        print(f"Error reading config file: {e}")
        return False