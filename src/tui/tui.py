from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Tree, Button, Label, Input, Checkbox, Select
from textual.containers import Container, Vertical, Horizontal, Grid

ANSWER_REGISTRY: dict[str, dict] = {
    "GitHub": {
        "template_repo": "https://github.com/EPFL-ENAC/template-repo.git",
        "branch": "main",
        "include_submodules": False,
        "new_repo_link": "https://github.com/EPFL-ENAC/new-repo.git",
    },
    "Projet": {
        "Lab_name": "My Lab",
        "project_name": "My Project",
        "project_description": "A description of my project.",
        "Domain_name_dev": "Development.com",
        "Domain_name_prod": "Production.com",
    }
}


SECTIONS = ["GitHub", "Projet"]

class TemplateTool(App):
    CSS_PATH = "tui.tcss"

    current_page = "GitHub"

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            tree: Tree[str] = Tree("Sections", id="menu")
            yield tree

            yield Vertical(id="content")

        with Horizontal(id="validation-bar"):
            yield Button("Validate", id="validate")

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
            
            content_container.mount(Label("GitHub Config", classes="title"))
            content_container.mount(Label("Template repository link :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_data.get("template_repo", ""), id="template_repo"))
            content_container.mount(Label("Branch :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_data.get("branch", ""), id="branch"))
            content_container.mount(Label("New repository link :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_data.get("new_repo_link", ""), id="new_repo_link"))
            content_container.mount(Label("Include submodules :", classes="subtitle"))
            content_container.mount(Checkbox(label="Include submodules", value=current_data.get("include_submodules", False), id="include_submodules"))

        elif page_key == "Projet":
            content_container.mount(Label("Project Config", classes="title"))
            current_data = ANSWER_REGISTRY.get("Projet", {})
            content_container.mount(Label("Project name :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_data.get("project_name", ""), id="project_name"))
            content_container.mount(Label("Lab name :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_data.get("Lab_name", ""), id="Lab_name"))
            content_container.mount(Label("Project description :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_data.get("project_description", ""), id="project_description"))
            content_container.mount(Label("Development domain name :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_data.get("Domain_name_dev", ""), id="Domain_name_dev"))
            content_container.mount(Label("Production domain name :", classes="subtitle"))
            content_container.mount(Input(placeholder=current_data.get("Domain_name_prod", ""), id="Domain_name_prod"))

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        event.stop()
        page_key = event.node.data
        if page_key in SECTIONS:
            self.current_page = page_key
            self.load_page(page_key)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "validate":
            # Placeholder for validation logic
            self.sub_title = "Validation complete!"
    
    def on_input_changed(self, event: Input.Changed) -> None:
        ANSWER_REGISTRY[self.current_page][event.input.id] = event.value
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        ANSWER_REGISTRY[self.current_page][event.checkbox.id] = event.value