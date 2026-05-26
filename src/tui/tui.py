from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Tree, Button, Label, Input, Checkbox, Select
from textual.containers import Container, Vertical, Horizontal, Grid
from scripts import validate_data, make_template_repo

ANSWER_REGISTRY: dict[str, dict] = {
    "GitHub": {
        "template_repo": "",
        "branch": "main",
        "include_submodules": False,
        "new_repo_link": "",
    },
    "Projet": {
        "Lab_name": "",
        "project_name": "",
        "project_description": "",
        "Domain_name_dev": "",
        "Domain_name_prod": "",
        "Domain_name_stage": "",
    },
    "CI/CD": {
        "keep_ci": True,
        "keep_pre_commits": True,
    },
    "Updates" :{
        "dependances": True,
        "pre-commit": True,
        "ci_cd": True,
    },
    "LLM": {
        "additional_prompt": ""
    }
}

PLACEHOLDER_REGISTRY: dict[str, dict] = {
    "GitHub": {
        "template_repo": "git@github.com:EPFL-ENAC/template-repo.git",
        "branch": "main",
        "include_submodules": False,
        "new_repo_link": "git@github.com:EPFL-ENAC/new-repo.git",
    },
    "Projet": {
        "Lab_name": "My Lab",
        "project_name": "My Project",
        "project_description": "A description of my project.",
        "Domain_name_dev": "Development.epfl.ch",
        "Domain_name_prod": "Production.epfl.ch",
        "Domain_name_stage": "Staging.epfl.ch",
    },
    "CI/CD": {
        "keep_ci": True,
        "keep_pre_commits": True,
    },
    "Updates": {
        "dependances": True,
        "pre-commit": True,
        "ci_cd": True,
    },
    "LLM": {
        "additional_prompt": ""
    }
}


SECTIONS = ["GitHub", "Projet", "CI/CD", "Updates", "LLM"]

class TemplateTool(App):
    CSS_PATH = "tui.tcss"

    current_page = "GitHub"
    in_process = False
    errors: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            tree: Tree[str] = Tree("Sections", id="menu")
            yield tree

            yield Vertical(id="content")

        with Vertical(id="validation-bar"):
            yield Button("Validate", id="validate")
            yield Static("", id="validation-errors")

    def on_mount(self) -> None:
        self.title = "ENAC-IT4R Dynamic Template Tool"
        self.sub_title = "Made with love by Quentin"
        
        tree = self.query_one("#menu", Tree)
        for page_key in SECTIONS:
            tree.root.add(page_key, page_key)
        tree.root.expand_all()
        
        self.load_page("GitHub")

    def load_page(self, page_key: str) -> None:
        content_container = self.query_one("#content", Vertical)
        content_container.remove_children()
        
        if(page_key == "GitHub"):
            current_data = ANSWER_REGISTRY.get("GitHub", {})
            current_placeholders = PLACEHOLDER_REGISTRY.get("GitHub", {})
            
            content_container.mount(Label("GitHub Config", classes="title"))
            content_container.mount(Label("Template repository link (*) :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("template_repo", ""), value=current_data.get("template_repo", ""), id="template_repo"))
            content_container.mount(Label("Branch :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("branch", ""), value=current_data.get("branch", ""), id="branch"))
            content_container.mount(Label("New repository link (*) :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("new_repo_link", ""), value=current_data.get("new_repo_link", ""), id="new_repo_link"))
            content_container.mount(Label("Include submodules :", classes="subtitle"))
            content_container.mount(Checkbox(label="Include submodules", value=current_data.get("include_submodules", False), id="include_submodules"))

        elif page_key == "Projet":
            current_data = ANSWER_REGISTRY.get("Projet", {})
            current_placeholders = PLACEHOLDER_REGISTRY.get("Projet", {})

            content_container.mount(Label("Project Config", classes="title"))
            content_container.mount(Label("Project name (*) :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("project_name", ""), value=current_data.get("project_name", ""), id="project_name"))
            content_container.mount(Label("Lab name :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("Lab_name", ""), value=current_data.get("Lab_name", ""), id="Lab_name"))
            content_container.mount(Label("Project description :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("project_description", ""), value=current_data.get("project_description", ""), id="project_description"))
            content_container.mount(Label("Development domain name :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("Domain_name_dev", ""), value=current_data.get("Domain_name_dev", ""), id="Domain_name_dev"))
            content_container.mount(Label("Production domain name :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("Domain_name_prod", ""), value=current_data.get("Domain_name_prod", ""), id="Domain_name_prod"))
            content_container.mount(Label("Staging domain name :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("Domain_name_stage", ""), value=current_data.get("Domain_name_stage", ""), id="Domain_name_stage"))
        
        elif page_key == "CI/CD":
            current_data = ANSWER_REGISTRY.get("CI/CD", {})
            current_placeholders = PLACEHOLDER_REGISTRY.get("CI/CD", {})

            content_container.mount(Label("CI/CD Config", classes="title"))
            content_container.mount(Checkbox(label="Keep existing CI/CD configuration", value=current_data.get("keep_ci", False), id="keep_ci"))
            content_container.mount(Checkbox(label="Keep existing pre-commit configuration", value=current_data.get("keep_pre_commits", False), id="keep_pre_commits"))
        
        elif page_key == "Updates":
            current_data = ANSWER_REGISTRY.get("Updates", {})
            current_placeholders = PLACEHOLDER_REGISTRY.get("Updates", {})

            content_container.mount(Label("Updates Config", classes="title"))
            content_container.mount(Checkbox(label="Update dependances", value=current_data.get("dependances", False), id="dependances"))
            content_container.mount(Checkbox(label="Update pre-commit configuration", value=current_data.get("pre-commit", False), id="pre-commit"))
            content_container.mount(Checkbox(label="Update CI/CD configuration", value=current_data.get("ci_cd", False), id="ci_cd"))

        elif page_key == "LLM":
            current_data = ANSWER_REGISTRY.get("LLM", {})
            current_placeholders = PLACEHOLDER_REGISTRY.get("LLM", {})

            content_container.mount(Label("LLM Config", classes="title"))
            content_container.mount(Label("Here is the prompt that will be used to clean the template repository:", classes="subtitle"))
            content_container.mount(Label("*Prompt for cleaning the template repository*", classes="subtitle"))
            content_container.mount(Label("Add an aditionnal prompt to the existing one:", classes="subtitle"))
            content_container.mount(Input(placeholder=current_placeholders.get("additional_prompt", ""), value=current_data.get("additional_prompt", ""), id="additional_prompt"))
        
        content_container.mount(Label("*Fields marked with (*) are required*", classes="footer"))

    def _clear_validation_state(self) -> None:
        self.query_one("#validation-errors", Static).update("")

        for widget_id in ("template_repo", "new_repo_link", "project_name"):
            matches = list(self.query(f"#{widget_id}"))
            if matches:
                matches[0].remove_class("invalid")

    def _display_validation_errors(self, errors: list[str]) -> None:
        error_panel = self.query_one("#validation-errors", Static)
        error_panel.update("Validation errors:\n" + "\n".join(f"- {error}" for error in errors))

        invalid_fields = {
            "GitHub: 'template_repo' is required.": "template_repo",
            "GitHub: 'template_repo' must be a valid GitHub repository link (e.g., git@github.com:username/repo.git)": "template_repo",
            "GitHub: 'new_repo_link' is required.": "new_repo_link",
            "GitHub: 'new_repo_link' must be a valid GitHub repository link (e.g., git@github.com:username/repo.git)": "new_repo_link",
            "Projet: 'project_name' is required.": "project_name",
        }

        for error in errors:
            widget_id = invalid_fields.get(error)
            if widget_id is None:
                continue

            matches = list(self.query(f"#{widget_id}"))
            if matches:
                matches[0].add_class("invalid")

    def _clear_invalid_style(self, widget_id: str) -> None:
        matches = list(self.query(f"#{widget_id}"))
        if matches:
            matches[0].remove_class("invalid")


    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        event.stop()
        page_key = event.node.data
        if page_key in SECTIONS:
            if self.current_page != page_key:
                self.current_page = page_key
                self.load_page(page_key)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "validate" and not self.in_process:
            self._clear_validation_state()
            errors = validate_data(ANSWER_REGISTRY)
            self.errors = errors

            if errors:
                self._display_validation_errors(errors)
            else:
                self.in_process = True
                self.query_one("#validation-errors", Static).update("Validation passed.")
                make_template_repo(ANSWER_REGISTRY)
                exit(1)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        ANSWER_REGISTRY[self.current_page][event.input.id] = event.value
        self._clear_invalid_style(event.input.id)
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        ANSWER_REGISTRY[self.current_page][event.checkbox.id] = event.value