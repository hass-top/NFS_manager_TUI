from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical
from screens.server_screen import ServerScreen
from screens.client_screen import ClientScreen
from screens.logs_screen import LogsScreen 
class MainMenu(Screen):
    """Main menu screen for NFS TUI."""
    CSS = """
    Screen {
        layout: grid;
        height: 100%;
        grid-size: 1 1;
        align: center middle;
    }
    Vertical.menu {
        align: center middle;
        width: 50%;
    }
    Button {
        width: 100%;
        margin: 1 0;
    }
    .title {
        margin-bottom: 2;
        text-align: center;
    }
    """
    def compose(self):
        """Create the main menu UI."""
        yield Header()
        yield Vertical(
            Static("NFS Configuration TUI", classes="title"),
            Button("Configure NFS Server", id="server", variant="primary"), 
            Button("Configure NFS Client", id="client", variant="success"),
            Button("see logs", id="logs", variant="warning"), 
            Button("Quit", id="quit", variant="error"),
            classes="menu"
        )
        yield Footer()

    def on_mount(self) -> None: 
        """Set focus to the first button when the screen loads."""
        self.query_one("#server", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "server":
            self.app.push_screen(ServerScreen())
        elif event.button.id == "client":
            self.app.push_screen(ClientScreen())
        elif event.button.id == "logs":
            self.app.push_screen(LogsScreen())
        elif event.button.id == "quit":
            self.app.exit()

    def on_key(self, event) -> None:
        """Handle key presses for navigation."""
        buttons = list(self.query("Button").results(Button))
        if not buttons:
            return
        focused = self.focused

        if event.key == "up":
            if focused in buttons:
                current_index = buttons.index(focused)
                if current_index > 0:
                    buttons[current_index - 1].focus()
                else:
                    buttons[-1].focus()  # Wrap to last button
            else:
                buttons[-1].focus()  # If no focus, go to last button
        elif event.key == "down":
            if focused in buttons:
                current_index = buttons.index(focused)
                if current_index < len(buttons) - 1:
                    buttons[current_index + 1].focus()
                else:
                    buttons[0].focus()  # Wrap to first button
            else:
                buttons[0].focus()  # If no focus, go to first button
        elif event.key == "enter":
            if focused and isinstance(focused, Button):
                focused.press() 
