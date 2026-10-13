# colors.py

class Colors:
    RESET = "\033[0m"
    DEFAULT = "\033[37m"  # white

    CODES: dict[str, str] = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "gray": "\033[90m",

        "orange": "\033[38;5;208m",
        "gold": "\033[38;5;220m",
        "purple": "\033[38;5;129m",
        "brown": "\033[38;5;94m",
        "lime": "\033[38;5;46m",
    }

    @classmethod
    def get(cls, color: str) -> str:
        return cls.CODES.get(color.lower(), "")
