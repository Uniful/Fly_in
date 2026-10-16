# colors.py
"""Provide ANSI color codes for Fly-In terminal output."""


class Colors:
    """
    Store and retrieve ANSI terminal color codes.

    The class maps color names from hub metadata to ANSI escape
    sequences used for colored simulation output. Unknown colors
    fall back to the default terminal color.
    """
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
        """
        Return the ANSI escape code for a color name.

        Parameters
        ----------
        color : str
            Color name requested by the hub metadata.

        Returns
        -------
        str
            Corresponding ANSI escape code, or the default color code
            if the requested color is not defined.
        """
        return cls.CODES.get(color.lower(), cls.DEFAULT)
