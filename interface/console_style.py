"""
AIE212 — Medical Diagnosis Expert System
interface/console_style.py

Responsibility: ANSI escape-code constants and formatting helpers for
terminal colour output.
"""


class ConsoleStyle:
    """
    ANSI escape-code constants for terminal colour and formatting.

    Usage
    -----
        ConsoleStyle.apply(text, ConsoleStyle.BOLD, ConsoleStyle.RED)
        ConsoleStyle.urgency("IMMEDIATE")
        ConsoleStyle.bold("PRIMARY DIAGNOSIS")
    """

    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"

    RED    = "\033[91m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    GREEN  = "\033[92m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"

    URGENCY_COLOR: dict = {
        "IMMEDIATE":   RED,
        "URGENT":      YELLOW,
        "SEMI_URGENT": BLUE,
        "NON_URGENT":  GREEN,
    }

    @staticmethod
    def apply(text: str, *codes: str) -> str:
        """Wrap text with one or more ANSI codes, then reset."""
        return "".join(codes) + text + ConsoleStyle.RESET

    @staticmethod
    def urgency(u: str) -> str:
        """Return an urgency string formatted in its associated colour."""
        color = ConsoleStyle.URGENCY_COLOR.get(u, "")
        return ConsoleStyle.apply(u, ConsoleStyle.BOLD, color)

    @staticmethod
    def bold(text: str) -> str:
        """Return text wrapped in BOLD."""
        return ConsoleStyle.apply(text, ConsoleStyle.BOLD)

    @staticmethod
    def dim(text: str) -> str:
        """Return text wrapped in DIM."""
        return ConsoleStyle.apply(text, ConsoleStyle.DIM)
