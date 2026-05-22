import os.path
from tui.tui import StaticAndLabelApp
from config import create_config, validate_config

if __name__ == "__main__":

    config_path = os.path.join(os.path.expanduser("~"),".config", "IT4R", "dynamic-template-tool", "config.json")
    config_exists = os.path.isfile(config_path)

    if not config_exists:
        create_config(config_path)
        exit(1)

    config_valid = validate_config(config_path)

    if not config_valid:
        print(f"Config file at {config_path} is invalid.")
        exit(1)

    app = StaticAndLabelApp()
    app.run()