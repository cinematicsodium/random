import json
from collections import Counter
from pathlib import Path

import fitz

from awards.formatting import Formatter

formatter = Formatter()


class DataCollector:
    data: dict[int, list[str]] = {}

    def extract(self, file: Path) -> None:
        with fitz.open(file) as doc:
            for page in doc:
                n: int = page.number
                self.data.setdefault(n, [])
                for field in page.widgets():
                    val = formatter.numerical(field.field_name)
                    key = formatter.clean(field.field_value)
                    self.data[val].append(key)
        print(f"Extracted all values from {file.name}")

    def process_files(self) -> None:
        folder: Path = Path("")
        for file in folder.glob("*.pdf"):
            self.extract(file)
        print(f"Extracted {len(self.data)} pages")

    def count_values(self) -> None:
        for key, val in self.data.items():
            counter = Counter(val)
            self.data[key] = dict(counter)
        print("Counted all values")

    def export_data(self) -> None:
        file: Path = Path("output.json")
        with file.open("w", encoding="utf-8") as jf:
            json.dump(self.data, jf, ensure_ascii=False, indent=4)
        print(f"Saved to {file}")
