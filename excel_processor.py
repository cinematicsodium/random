from pathlib import Path
from time import sleep

import pandas as pd
from rich.console import Console
from rich.traceback import install

install(show_locals=True)
console = Console()

identifier_cols = ["name", "UUID", "position", "company", "location"]


def generate_new(file_path: Path) -> Path:
    """
    Generate a unique output file path by modifying the original stem.
    """
    new_path = file_path.with_stem(f"{file_path.stem}_js")
    if new_path.exists():
        counter = 1
        while new_path.exists():
            new_path = new_path.with_stem(f"{new_path.stem}_js_{counter}")
            counter += 1
    console.print(f"[blue]Output Path: {new_path.name}[/blue]")
    return new_path


def merge_employee_functions(input_file: Path):
    """
    Merge employee functions from an Excel file.
    """
    with console.status("Loading Excel file..."):
        sleep(1.5)
        df = pd.read_excel(input_file, engine="openpyxl")

        df[identifier_cols] = df[identifier_cols].apply(
            lambda col: col.astype(str).str.strip()
        )
        df = df.dropna(subset=identifier_cols, how="all")

        df.sort_values(by=identifier_cols, inplace=True)

        merged_df = df.groupby(identifier_cols, as_index=False)["function"].agg(
            lambda funcs: "\n\n".join(
                f.strip() for f in funcs if isinstance(f, str) and f.strip()
            )
        )

        output_file = generate_new(input_file)
        # Write the merged data to a new Excel file
        merged_df.to_excel(output_file, index=False, engine="openpyxl")

        print(f"Data merged successfully. Output saved to {output_file}.")


def merge_dataframes(data_frames: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple DataFrames on common columns.
    """
    with console.status("Merging files..."):
        sleep(1.5)
        common_columns = set.intersection(*[set(df.columns) for df in data_frames])
        merged_df = pd.concat(
            [df[common_columns] for df in data_frames],
            ignore_index=True,
            join="outer",
        )
        merged_df.to_excel("merged_files_js.xlsx", index=False)
    console.print("\n\n[green]All files merged successfully.[/green]")


def main():
    """
    Main function to execute the script.
    """
    if True:
        console.print("\n\n[]Update identifier_cols\n\n")
        exit()
    try:
        data_frames: list[pd.DataFrame] = []
        all_processed: bool = True
        folder: Path = Path(None)
        for path in folder.iterdir():
            if path.is_file() and path.suffix == ".xlsx":
                try:
                    console.print(
                        f"\n\n[dark_slate_gray2]File: {path.name}[/dark_slate_gray2]"
                    )

                except Exception as e:
                    console.print(f"\n[orange1]Error:\n{e}[/orange1]")
                    all_processed = False
                    sleep(5)

        if all_processed and data_frames:
            merge_dataframes(data_frames)
    except Exception as e:
        console.print(f"\n[orange1]Error:[/orange1]\n{e}")
        sleep(5)


if __name__ == "__main__":
    main()
