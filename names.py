from rich.traceback import install

install(show_locals=True, width=200)

import re

from nameformatter import NameFormatter


class Formatter:
    @staticmethod
    def clean(text: str) -> str | None:
        text = str(text).strip()
        text = text.encode("ascii", errors="ignore").decode("ascii")
        text = re.sub(r"[\r\t]+", lambda m: "\n" if m.group(0) == "\r" else " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip() if text else None

    @staticmethod
    def key(text: str) -> str | None:
        text = Formatter.clean(text)
        if not text:
            return None

        matches = re.findall(r"[a-zA-Z0-9]+", text)
        return "_".join(matches).lower()

    @staticmethod
    def name(text: str) -> str | None:
        text = Formatter.clean(text)
        if not text:
            return None
        return NameFormatter(text).format_last_first()

    @staticmethod
    def is_list_item(line: str) -> bool:
        return bool(re.match(r"^[a-zA-Z0-9]{1,3}\.", line))

    @staticmethod
    def justification(text: str) -> str | None:
        text = Formatter.clean(text)
        if not text:
            return None

        text = text.replace('"', "'")
        lines = []
        for line in filter(None, map(str.strip, text.split("\n"))):
            prefix = (
                "> "
                if line and line[0].isalnum() and not Formatter.is_list_item(line)
                else "    "
            )
            lines.append(f"{prefix}{line}")
        return f'"{"\n".join(lines)}"'

    @staticmethod
    def extract_int(text: str) -> int:
        num = 0
        text = Formatter.clean(text)
        if not text:
            return None

        match = re.search(r"([\d,]*\d(?:\.\d+)?)", text)
        if match:
            num = float(match.group(1).replace(",", ""))
            if not num.is_integer():
                raise ValueError(f"Extracted value '{num}' is not an integer")
        return int(num)

    @staticmethod
    def standardized_org_div(text: str) -> str | None:
        text = Formatter.clean(text)
        if not text:
            return None

        return text.replace("-", "").replace(" ", "").lower()

    @staticmethod
    def _fmtpart(part: str) -> str | None:
        part = re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$", "", part)
        part = re.sub(r"[^a-zA-Z0-9]+", "-", part).upper()
        part = re.sub(r"-+", "-", part)
        return part if part else None

    @staticmethod
    def pay_plan(text: str) -> str | None:
        text = Formatter.clean(text)
        if not text:
            return None

        parts = [
            Formatter._fmtpart(part)
            for part in text.split()
            if Formatter._fmtpart(part)
        ]
        return "-".join(parts) if parts else None

formatter = Formatter()

def __test():
    text = "  This is a test text with   multiple spaces, tabs\tand newlines.\n\n\n"
    test_map = {
        "clean": formatter.clean(text),
        "key": formatter.key(text),
        "name": formatter.name("John Doe"),
        "is_list_item": formatter.is_list_item("1. List item"),
        "justification": formatter.justification("   This is a justification text."),
        "extract_int": [
            formatter.extract_int("The number is 1234."),
            type(formatter.extract_int("The number is 1234.")),
        ],
        "standardized_org_div": formatter.standardized_org_div("Org - Division"),
        "pay_plan": formatter.pay_plan("Pay Plan Example 123"),
    }
    for key, value in test_map.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    __test()

..................................................

TITLES: list[str] = [
    "dr",
    "mr",
    "mrs",
    "ms",
    "prof",
    "phd",
    "miss",
    "associate",
    "administrator",
    "manager",
    "analyst",
]

NAME_PARTICLES = [
    "mc",
    "st",
    "st.",
    "de",
    "da",
    "di",
    "du",
    "la",
    "le",
    "el",
    "lo",
    "am",
    "op",
    "te",
    "zu",
    "zu",
    "im",
    "af",
    "av",
    "al",
    "ov",
    "ev",
]

..................................................
from rich.traceback import install

install(show_locals=True, width=200)

import re

from namecomponents import NAME_PARTICLES, TITLES

ENCLOSED_PATTERN = re.compile(r"(['\"])([a-zA-Z]{1,12})\1|(\()([a-zA-Z]{1,32})(\))")
CREDENTIALS_PATTERN = re.compile(r"\b[a-zA-Z]{2,4}\.(?:[a-zA-Z])?\.?")
ABBREVIATION_PATTERN = re.compile(r"\b[A-Za-z]\.")
ALPHABET_PATTERN = re.compile(r"[a-zA-Z]+")
CAPITALIZED_PATTERN = re.compile(r"[A-Z]")


class NameFormatter:
    def __init__(self, name_string: str):
        self.name_string = name_string
        self.name_parts: list[str] = self._name_parts()
        self.first_name = None
        self.last_name = None
        self.full_name = None

    def is_enclosed(self, part: str) -> bool:
        return ENCLOSED_PATTERN.match(part) is not None

    def is_abbreviation(self, part: str) -> bool:
        return ABBREVIATION_PATTERN.fullmatch(part) is not None

    def is_credential(self, part: str) -> bool:
        return CREDENTIALS_PATTERN.fullmatch(part) is not None

    def _is_valid(self, name_part: str) -> bool:
        part_lower = name_part.lower()
        if part_lower in NAME_PARTICLES:
            return True

        normalized = "".join(ALPHABET_PATTERN.findall(name_part)).lower()
        if normalized in TITLES:
            return False

        if (
            self.is_credential(name_part)
            or self.is_enclosed(name_part)
            or self.is_abbreviation(name_part)
            or len(name_part) == 1
        ):
            return False

        return True

    def _name_parts(self) -> list[str]:
        parts = self.name_string.split(" ")
        for idx, part in enumerate(parts):
            if part.lower() == "for":
                parts = parts[idx + 1 :]
                break
        return [part for part in parts if self._is_valid(part)]

    def extract_names_from_five_parts(self):
        if self.first_name and self.last_name:
            return

        if len(self.name_parts) == 5:
            first_name, last_name, preposition = self.name_parts[:3]
            if preposition == "for":
                self.first_name = first_name
                self.last_name = last_name

    def extract_names_from_four_parts(self):
        if self.first_name and self.last_name:
            return

        if len(self.name_parts) == 4:
            first_name, preposition, article, noun = self.name_parts
            if (
                preposition.lower() in NAME_PARTICLES
                and article.lower() in NAME_PARTICLES
            ):
                self.first_name = first_name
                self.last_name = f"{preposition} {article} {noun}"

    def extract_names_from_three_parts(self):
        if self.first_name and self.last_name:
            return

        if len(self.name_parts) == 3:
            first_name, preposition, article = self.name_parts
            if preposition.lower() in NAME_PARTICLES:
                self.first_name = first_name
                self.last_name = f"{preposition} {article}"

    def extract_names_from_two_parts(self):
        if self.first_name and self.last_name:
            return

        if len(self.name_parts) == 2:
            first_name, last_name = self.name_parts
            if first_name.endswith(","):
                last_name, first_name = first_name, last_name
            self.first_name = first_name.replace(",", "").strip()
            self.last_name = last_name.replace(",", "").strip()

    def extract_names(self):
        self.extract_names_from_five_parts()
        self.extract_names_from_four_parts()
        self.extract_names_from_three_parts()
        self.extract_names_from_two_parts()

    def set_full_name(self):
        if self.first_name and self.last_name:
            full_name = ", ".join([self.last_name, self.first_name])
            capitalized_count: int = len(CAPITALIZED_PATTERN.findall(full_name))
            if not (2 <= capitalized_count <= 5):
                full_name = full_name.title()
            self.full_name = full_name

    def format_last_first(self) -> str | None:
        self.extract_names()
        self.set_full_name()
        if self.full_name:
            return self.full_name
        return self.name_string
