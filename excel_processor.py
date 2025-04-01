from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import Optional

import openpyxl
import pandas as pd
from rich.console import Console
from rich.traceback import install

install(show_locals=True)
console = Console()


@dataclass
class ExcelProcessor:
    """Processes Excel files by extracting, merging, and saving data."""

    file_path: Path

    def extract_data(self) -> Optional[pd.DataFrame]:
        """Extract data from the Excel file."""
        with console.status(f"{self.file_path.name}: Extracting data..."):
            sleep(1.5)
            try:
                wb = openpyxl.load_workbook(self.file_path)

                sheet = wb["TDA"]

                table = sheet.tables["TBLTDA"]

                df = []
                for row in sheet[table.ref]:
                    row_data = []
                    for cell in row:
                        row_data.append(cell.value)
                    df.append(row_data)

                df = pd.DataFrame(df[1:], columns=df[0])

                console.print("[green]Data extracted.[/green]")

                return df
            except Exception as e:
                console.print(
                    f"[orange1]Unable to read the Excel file: {str(e)}[/orange1]"
                )
                return None

    def merge_data(self) -> Optional[pd.DataFrame]:
        """Merge data by grouping by LastFirst and joining function values."""
        if (df := self.extract_data()) is None:
            return None
        with console.status(f"{self.file_path.name}: Merging extracted data..."):
            sleep(1.5)
            try:
                filtered_df = df[
                    (df["Unique Employee Identification  Number"].notnull())
                    & (~df["LastFirst"].str.contains("vacant", case=False))
                ]
                data = (
                    filtered_df.groupby("LastFirst")["Workload"]
                    .apply(lambda x: "\n".join(x))
                    .reset_index()
                )
                console.print("[green]Data merged.[/green]")
                return data
            except Exception as e:
                console.print(f"[orange1]Error merging data: {str(e)}[/orange1]")
                return None

    def generate_path(self) -> Path:
        """Generate a unique output file path by modifying the original stem."""
        new_path = self.file_path.with_stem(f"{self.file_path.stem}_js")
        if new_path.exists():
            counter = 1
            while new_path.exists():
                new_path = new_path.with_stem(f"{new_path.stem}_js_{counter}")
                counter += 1
        console.print(f"[blue]Output Path: {new_path.name}[/blue]")
        return new_path

    def save_data(self, data: pd.DataFrame) -> None:
        """Save the merged data to a new Excel file."""
        output_path = self.generate_path()
        with console.status("Saving data..."):
            sleep(1.5)
            try:
                data.to_excel(output_path, index=False)
                console.print(
                    f"[green]Results saved to {output_path} successfully.[/green]"
                )
            except Exception as e:
                console.print(f"[orange1]Error saving to Excel: {str(e)}[/orange1]")

    def run(self) -> Optional[pd.DataFrame]:
        """Extract, merge, and save data."""
        data = self.merge_data()
        if data is None:
            return None
        self.save_data(data)
        return data


def main():
    try:
        data_frames: list[pd.DataFrame] = []
        all_processed: bool = True
        folder: Path = Path()
        for path in folder.iterdir():
            if path.is_file() and path.suffix == ".xlsx":
                try:
                    console.print(
                        f"\n\n[dark_slate_gray2]File: {path.name}[/dark_slate_gray2]"
                    )
                    processor = ExcelProcessor(path)
                    data = processor.run()
                    if data is None:
                        all_processed = False
                    data_frames.append(data)
                except Exception as e:
                    console.print(f"\n[orange1]Error:\n{e}[/orange1]")
                    all_processed = False
                    sleep(5)

        if all_processed and data_frames:
            with console.status("Merging files..."):
                sleep(1.5)
                common_columns = set.intersection(
                    *[set(df.columns) for df in data_frames]
                )
                merged_df = pd.concat(
                    [df[common_columns] for df in data_frames],
                    ignore_index=True,
                    join="outer",
                )
                merged_df.to_excel("merged_files_js.xlsx", index=False)
            console.print("\n\n[green]All files merged successfully.[/green]")
    except Exception as e:
        console.print(f"\n[orange1]Error:[/orange1]\n{e}")
        sleep(5)


#
# ChatGPT Example 1
#
import pandas as pd


def merge_employee_functions(input_file: str, output_file: str):
    # Read the data from the Excel file
    df = pd.read_excel(input_file)

    # Define columns that uniquely identify each employee
    identifier_cols = ["name", "UUID", "position", "company", "location"]

    # Group by the identifier columns and merge the functions with double newlines as separator
    merged_df = df.groupby(identifier_cols, as_index=False)["function"].agg(
        lambda funcs: "\n\n".join(funcs)
    )

    # Write the merged data to a new Excel file
    merged_df.to_excel(output_file, index=False)

    print(f"Data merged successfully. Output saved to {output_file}.")


if __name__ == "__main__":
    # Specify input and output file names
    input_excel = "input.xlsx"
    output_excel = "merged_output.xlsx"

    merge_employee_functions(input_excel, output_excel)

#
# ChatGPT Example 2
#
import pandas as pd


def merge_employee_functions(input_file: str, output_file: str):
    # Read the data from the Excel file using openpyxl engine, ensuring formula evaluation
    df = pd.read_excel(input_file, engine="openpyxl")

    # Strip whitespace and drop rows with incomplete identifiers
    identifier_cols = ["name", "UUID", "position", "company", "location"]
    df[identifier_cols] = df[identifier_cols].apply(
        lambda col: col.astype(str).str.strip()
    )
    df = df.dropna(subset=identifier_cols)

    # Ensure deterministic order (optional)
    df.sort_values(by=identifier_cols + ["function"], inplace=True)

    # Group and merge function field
    merged_df = df.groupby(identifier_cols, as_index=False)["function"].agg(
        lambda funcs: "\n\n".join(
            f.strip() for f in funcs if isinstance(f, str) and f.strip()
        )
    )

    # Write the merged data to a new Excel file
    merged_df.to_excel(output_file, index=False, engine="openpyxl")

    print(f"Data merged successfully. Output saved to {output_file}.")


#
# Deepseek Example
#
import pandas as pd

# Read the Excel file into a DataFrame
df = pd.read_excel("input.xlsx")

# Group by UUID and aggregate the data
merged_df = (
    df.groupby("UUID")
    .agg(
        {
            "name": "first",
            "position": "first",
            "company": "first",
            "location": "first",
            "function": lambda x: "\n\n".join(x),
        }
    )
    .reset_index()
)

# Reorder the columns to match the original structure
merged_df = merged_df[["name", "UUID", "position", "company", "location", "function"]]

# Write the merged data to a new Excel file
merged_df.to_excel("output.xlsx", index=False)
