from textual.screen import Screen
from textual.widgets import Button, Input, Static, Header, Footer, Select 
from textual.containers import Vertical
from utils.helpers import run_script
import os  

class ServerScreen(Screen):
    """Screen for configuring NFS server."""

    CSS = """
    Vertical {
        align: center middle;
    }
    Input , Select {
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
    Select:focus {
        border: solid $accent;
        background: $surface;
    }
    """

    def compose(self):
        """Create the server configuration UI."""
        yield Header()
        yield Vertical(
            Static("Configure NFS Server", classes="title"),            
            Static("Enter directory to export (e.g., /srv/nfs):"),
            Input(placeholder="/srv/nfs", id="export_path"),
            Static("Enter client IP (default * ):"),
            Input(placeholder="89.207.132.170 or  1.1.1.0/24 or *", id="client_ip"),
            Static("Enter access mode (default rw)"),
            Input(placeholder="rw or ro", id="access_mode"),
            Static("Enter sync mode (default sync):"),
            Input(placeholder="sync or async", id="sync_mode"),
            Static("Enter subtree option (default no_subtree_check):"),
            Input(placeholder="no_subtree_check or subtree_check", id="subtree_option"),
            Button("Setup Server", id="setup", variant="primary"),
            Button("Back", id="back", variant="warning"),
            Static("", id="output", classes="output"),
           
        )
        yield Footer()



    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "setup":
            export_path = self.query_one("#export_path", Input).value.strip()
            client_ip = self.query_one("#client_ip", Input).value.strip() or "*"  
            access_mode = self.query_one("#access_mode", Input).value.strip() or "rw"
            sync_mode = self.query_one("#sync_mode", Input).value.strip() or "sync"
            subtree_option = self.query_one("#subtree_option", Input).value.strip() or "no_subtree_check"
            if not export_path:
                self.query_one("#output", Static).update("Error: Export path cannot be empty.")

                return
            result = run_script("./bash/nfs_server.sh",

            export_path,
            client_ip,
            access_mode,
            sync_mode,
            subtree_option
        )
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
