from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Tree, Button, Label, Input, Checkbox, Select
from textual.containers import Container, Vertical, Horizontal, Grid

PAGE_REGISTRY: dict[str, dict] = {
    "GitHub": {
        "title": "GitHub",
        "content": [
            {"type": "label", "label": "Welcome to the GitHub Page", "classes": "title"},

            {"type": "input", "label": "Template repository URL", "placeholder": "https://github.com/user/repo.git"},

            {"type": "input", "label": "Branch", "placeholder": "main"},
            {"type": "checkbox", "label": "Include submodules"},

            {"type": "input", "label": "New repository link", "placeholder": "https://github.com/user/new-repo.git"},
        ]
    },
}

class TemplateTool(App):
    CSS_PATH = "tui.tcss"

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
        for page_key, page_data in PAGE_REGISTRY.items():
            tree.root.add(page_data["title"], page_key)
        tree.root.expand_all()
        
        self.load_page("GitHub")

    def load_page(self, page_key: str) -> None:
        if page_key not in PAGE_REGISTRY:
            return
        page_data = PAGE_REGISTRY[page_key]
        content_container = self.query_one("#content", Vertical)
        content_container.remove_children()
        
        for widget_config in page_data["content"]:
            widget_type = widget_config["type"]
            if widget_type == "label":
                content_container.mount(Label(widget_config["label"], classes=widget_config.get("classes", "")))
            elif widget_type == "input":
                input_row = Horizontal(classes="input-row")
                content_container.mount(input_row)
                input_row.mount(Label(widget_config["label"], classes="input-label"))
                input_row.mount(Input(placeholder=widget_config.get("placeholder", "")))
            elif widget_type == "checkbox":
                content_container.mount(Checkbox(widget_config["label"]))
            elif widget_type == "select":
                select_row = Horizontal(classes="input-row")
                content_container.mount(select_row)
                select_row.mount(Label(widget_config["label"], classes="input-label"))
                options = widget_config.get("options", [])
                select_row.mount(Select(options, allow_blank=False))
            elif widget_type == "grid":
                grid = Grid(classes="content-grid")
                cols = widget_config.get("cols", 2)
                grid.styles.grid_columns = [f"1fr" for _ in range(cols)]
                content_container.mount(grid)
                for item in widget_config["items"]:
                    grid.mount(Label(item["label"], classes=item.get("classes", "")))

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        event.stop()
        page_key = event.node.data
        if page_key in PAGE_REGISTRY:
            self.load_page(page_key)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "validate":
            # Placeholder for validation logic
            self.sub_title = "Validation complete!"
