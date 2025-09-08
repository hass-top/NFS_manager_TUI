from textual.app import App, ComposeResult
from screens.main_menu import MainMenu
from textual.widgets import Header , Footer

class NFSApp(App):
    
    """TUI CSS place"""
    CSS = """
    Screen {
        align: center middle;
    }
    """

    """THE FIRST SCREEN TO BE SHOWN""" 
    def on_mount(self) -> None:
         self.push_screen(MainMenu()) 

    """STRUCTURE OF THE APP""" 
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True) 
        
        yield Footer () 

if __name__ == "__main__":
    NFSApp().run()
