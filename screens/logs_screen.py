from calendar import c
from textual.screen import Screen 
from textual.widgets import Button, Static, Header, Footer, Input 
from textual.containers import Vertical , Horizontal
from utils.helpers import run_script_test, run_mount_nfs

class LogsScreen(Screen):
    """Screen for displaying the contents of /etc/exports and NFS client mounts."""

    CSS  = """
#logs_horizontal {
    width: 100%;
    height: 70%;

    padding: 1;
}

#exports_section, #clients_section {
    width: 50%;
    align: center top;
    padding: 1;
}

.output {
    max-height: 25;
    overflow-y: auto;
    width: 95%;
    background: $surface;
    border: round $accent;
    padding: 1;
    color: $text;
    text-align: left;
}


  Button {
       width: 20;
       padding: 1 2;
       margin: 0;
    }


.title {
    text-align: center;
    margin-bottom: 1;
    color: $accent;
}

Static {
    color: $text;
    background: $surface;
    margin: 1 0; 
}

#buttons_section {
    width: 100%;
    height: auto;
    align: center middle;
    padding: 1;
    layout: horizontal;   
    }



"""

    def compose(self):
        yield Header()

        yield Horizontal(
            Vertical(
            Static("NFS Exports (/etc/exports)", classes="title"),
            Static("", id="exports_output", classes="output"),
            Static("remove export (e.g., /srv):"), 
            Input(placeholder="/test", id="remove_export_input"),
            id="exports_section",
            ),
            Vertical(
            Static("NFS Client Mounts", classes="title"),
            Static("", id="clients_output", classes="output"),
            Static("Unmount client (e.g., /mnt/nfs_share):"), 
            Input(placeholder="/test", id="remove_client_input"), 
            id="clients_section",
            ),
        id="logs_horizontal",
        )

        # Buttons at the bottom
        yield Vertical(
            Button("Remove Export", id="remove_export", variant="error"),
            Button("Refresh", id="refresh", variant="primary"),
            Button("Back", id="back", variant="warning"),
            Button("remove client" , id="remove_client" , variant="error"), 
            id="buttons_section",
        )
        yield Footer()

    def read_exports(self) -> None:
      
        result = run_script_test("cat", "/etc/exports")

        if result.startswith("[-] Error"):
            self.query_one("#exports_output", Static).update(result)
        elif not result.strip():
            self.query_one("#exports_output", Static).update("No exports configured in /etc/exports.")
        else:
            self.query_one("#exports_output", Static).update(result)

    def list_nfs_clients(self) -> None: 
        client_result = run_mount_nfs()

        self.query_one("#clients_output", Static).update(client_result)

    def on_mount(self) -> None:
        self.read_exports()
        self.list_nfs_clients()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "refresh":
            self.read_exports()
            self.list_nfs_clients()
        elif event.button.id == "remove_export": 
            self.remove_tt()
        elif event.button.id == "remove_client": 
            self.remove_client() 
    def remove_tt(self) -> None:
        
        export_path = self.query_one("#remove_export_input", Input).value.strip()

        # Validate the input
        if not export_path:
            self.query_one("#exports_output", Static).update("Error: No export path provided.")
            return
        if not export_path.startswith("/"):
            self.query_one("#exports_output", Static).update("Error: Path must start with '/'.")
            return

        # Escape the path for sed regex
        escaped_path = export_path.replace("/", r"\/")
        sed_pattern = fr'\|^{escaped_path} |d'

        # Execute the sed command to remove lines starting with the export path
        sed_result = run_script_test("sed", "-i", sed_pattern, "/etc/exports")
        if sed_result.startswith("[-] Error"):
            self.query_one("#exports_output", Static).update(f"Error removing {export_path} export: {sed_result}")
            return

        # Execute exportfs -ra to refresh NFS exports
        exportfs_result = run_script_test("exportfs", "-ra")
        if exportfs_result.startswith("[-] Error"):
            self.query_one("#exports_output", Static).update(f"Error refreshing exports: {exportfs_result}")
            return

        # Refresh the exports display after modification
        self.read_exports()
        self.query_one("#exports_output", Static).update(f"Successfully removed {export_path} export and refreshed NFS.")

    def remove_client(self) -> None:
        """Unmount a client safely."""
        client_path = self.query_one("#remove_client_input", Input).value.strip()
        if not client_path:
            self.query_one("#clients_output", Static).update("Error: No client path provided.")
            return

        # Call lazy unmount with force as needed
        result = run_script_test("umount", "-l", client_path)
        if result.startswith("[-] Error"):
            self.query_one("#clients_output", Static).update(f"Error unmounting {client_path}: {result}")
            return

        rm_result = run_script_test("rm", "-rf", client_path)
        if rm_result.startswith("[-] Error"):
            self.query_one("#clients_output", Static).update(f"Error deleting {client_path}: {rm_result}")
            return
        self.query_one("#clients_output", Static).update(f"Successfully unmounted {client_path}")
        self.list_nfs_clients()
    def on_key(self, event) -> None:
        """Handle key presses for navigation."""
        focusable_widgets = list(self.query("Button, Input").results())
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

