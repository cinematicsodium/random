from datetime import datetime
from rich.console import Console
from rich.traceback import install
from rich import print as rprint

install(show_locals=True)

console = Console

class Logger:
    def __init__(self, log_level="INFO"):
        self.log_level = log_level

    def _log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "PASS":
            rprint(f"[{timestamp}]")
            return

        style = "bright_red" if level == "WARNING" else "bright_cyan"
        console.print(f"[{timestamp}]  [{level}]  {message}", style=style)

    def debug(self, message):
        self._log("DEBUG", message)

    def info(self, message):
        self._log("INFO", message)

    def warning(self, message):
        self._log("WARNING", message)

    def error(self, message):
        self._log("ERROR", message)

    def critical(self, message):
        self._log("CRITICAL", message)

    def PASS(self):
        self._log("PASS", "")

logger = Logger()
