# Logger class for Logs!

import logging
import sys
class Log:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    ORANGE = "\033[38;5;214m"

    def __init__(self):
        self.logger = logging.getLogger("CustomLogger")
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        logging.addLevelName(25, "SUCCESS")
    
    def success(self, message):
        """Log a success message in green."""
        self.logger.log(25, f"{self.GREEN}[SUCCESS] {message}{self.RESET}")

    def info(self, message):
        """Log an info message in yellow."""
        self.logger.info(f"{self.YELLOW}[INFO] {message}{self.RESET}")

    def error(self, message, kill=False):
        """Log an error message in red."""
        self.logger.error(f"{self.RED}[ERROR] {message}{self.RESET}")
        if kill == True: # If the error requires killing the program check param. 
            sys.exit(1)
        else:
            pass
    
    def warning(self, message):
        """Log an warning message in orange."""
        self.logger.warning(f"{self.ORANGE}[WARNING] {message}{self.RESET}")



        