import os


def get_vars():
    with open(os.path.join(os.path.expanduser("~"),".config", "IT4R", "dynamic-template-tool", "config.json"), "r") as f:
        config = f.read()
    return config