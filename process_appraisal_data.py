from datetime import datetime
from pathlib import Path
import os


DOWNLOADS_DIRECTORY: str
PAMS_DIRECTORY: str
FILE_PREFIX: str


def get_file_creation_date(file_path: str) -> str:
    timestamp = os.path.getctime(file_path)
    date_created = datetime.fromtimestamp(timestamp)
    print(f"{timestamp=}")
    print(f"{date_created=}")
    return str(date_created.date())


def rename_and_move_file(file_path: str):
    date_created = get_file_creation_date(file_path)
    new_name = f"{FILE_PREFIX} _ {date_created}{Path(file_path).suffix}"
    new_path: str = os.path.join(PAMS_DIRECTORY, new_name)
    os.rename(file_path, new_path)
    print(f"renamed file: {new_name}")


def process_appraisal_data() -> None:
    print("\nstart...\n")
    try:
        if not os.path.isdir(DOWNLOADS_DIRECTORY):
            raise ValueError(f"invalid directory: {DOWNLOADS_DIRECTORY}")

        files: list[str] = [
            file
            for file in Path(DOWNLOADS_DIRECTORY).iterdir()
            if "pams-appraisal" in Path(file).name.lower()
        ]
        if not files:
            raise ValueError("No PAMS appraisal files found.")

        for file_path in files:
            try:
                rename_and_move_file(file_path)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    print("\nfinished...\n")


if __name__ == "__main__":
    process_appraisal_data()
