from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Tree, Button
from textual.containers import Container, Vertical, Horizontal

class TemplateTool(App):
    CSS_PATH = "tui.tcss"

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            tree: Tree[str] = Tree("Sections", id="menu")
            tree.root.expand()
            yield tree

            yield Static("Content will be displayed here.", id="content")

        with Horizontal(id="validation-bar"):
            yield Button("Validate", id="validate")

    def on_mount(self) -> None:
        self.title = "ENAC-IT4R Dynamic Template Tool"
        self.sub_title = "Made with love by Quentin"
