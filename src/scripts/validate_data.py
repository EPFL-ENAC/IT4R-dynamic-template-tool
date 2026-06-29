


import re


def validate_data(data):
    errors = []
    
    # Validate GitHub section
    github_data = data.get("GitHub", {})
    if not github_data.get("template_repo"):
        errors.append("GitHub: 'template_repo' is required.")
    if not github_data.get("new_repo_link"):
        errors.append("GitHub: 'new_repo_link' is required.")
    
    # Validate Projet section
    projet_data = data.get("Projet", {})
    if not projet_data.get("project_name"):
        errors.append("Projet: 'project_name' is required.")

    github_repo_re = r"^(git\@github\.com:[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\.git)$"
    if github_data.get("template_repo") and not re.match(github_repo_re, github_data["template_repo"]):
        errors.append("GitHub: 'template_repo' must be a valid GitHub repository link (e.g., git@github.com:username/repo.git)")
    if github_data.get("new_repo_link") and not re.match(github_repo_re, github_data["new_repo_link"]):
        errors.append("GitHub: 'new_repo_link' must be a valid GitHub repository link (e.g., git@github.com:username/repo.git)")
    
    
    return errors