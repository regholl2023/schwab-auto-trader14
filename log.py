# Logger class for Logs!

import logging
class Log:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

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

    def error(self, message):
        """Log an error message in red."""
        self.logger.error(f"{self.RED}[ERROR] {message}{self.RESET}")
        