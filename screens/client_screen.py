from textual.screen import Screen
from textual.widgets import Button, Input, Static, Header, Footer
from textual.containers import Vertical
from utils.helpers import run_script
import os 
class ClientScreen(Screen):
    """Screen for configuring NFS client."""

    CSS = """
    Vertical {
        align: center middle;
    }
    Input {
        margin: 1 0;
        width: 50;
    }
    .output {
        margin-top: 1;
        max-height: 10;
        overflow-y: auto;
    }
    Button:focus {
        border: solid $accent;
        background: $accent-darken-1;
    }
    Input:focus {
        border: solid $accent;
        background: $surface;
    }
    """

    def compose(self):
        """Create the client configuration UI."""
        yield Header()
        yield Vertical(
            Static("Configure NFS Client", classes="title"),
            Static("Enter NFS server IP (e.g., 192.168.1.100):"),
            Input(placeholder="192.168.1.100", id="server_ip"),
            Static("Enter server export path (e.g., /srv/nfs):"),
            Input(placeholder="/srv/nfs", id="export_path"),
            Static("Enter local mount point (e.g., /mnt/nfs):"),
            Input(placeholder="/mnt/nfs", id="mount_point"),
            Button("Mount Share", id="mount", variant="primary"),
            Button("Back", id="back", variant="warning"),
            Static("", id="output", classes="output"),
            )
        yield Footer()

    def on_mount(self) -> None:
        """Set initial focus to the first input field."""
        self.query_one("#server_ip", Input).focus()

   
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "mount":
            server_ip = self.query_one("#server_ip", Input).value.strip()
            export_path = self.query_one("#export_path", Input).value.strip()
            mount_point = self.query_one("#mount_point", Input).value.strip()
            if not all([server_ip, export_path, mount_point]):
                self.query_one("#output", Static).update("Error: All fields are required.")
                return
            result = run_script("./bash/nfs_client.sh", server_ip, export_path, mount_point)
            self.query_one("#output", Static).update(result)
        elif event.button.id == "back":
            self.app.pop_screen()

    def on_key(self, event) -> None:
        """Handle key presses for navigation across input and buttons."""
        focusable_widgets = list(self.query("Input, Button").results())
        if not focusable_widgets:
            return
        focused = self.focused

        if focused and event.key in ("up", "down"):
            current_index = focusable_widgets.index(focused)
            new_index = current_index
            if event.key == "up":
                new_index = (current_index - 1) % len(focusable_widgets)
            elif event.key == "down":
                new_index = (current_index + 1) % len(focusable_widgets)
            focusable_widgets[new_index].focus()
        elif focused and event.key == "enter" and isinstance(focused, Button):
            focused.press()
