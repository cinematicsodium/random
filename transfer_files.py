import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from typing import Optional

from rich.console import Console


@dataclass
class FileTransfer:
    file_path: Path
    target_directory: Path
    category: str = ""

    def __str__(self) -> str:
        self.category = self.category if self.category else None
        return (
            f"\n\n"
            f"file:             {self.file_path.name}\n"
            f"target_directory: {self.target_directory}\n"
            f"category:         {self.category}"
        )

    def validate_paths(self) -> None:
        """Checks if the target directory and file path are valid."""
        if not (self.target_directory.exists() and self.target_directory.is_dir()):
            raise ValueError(
                f"Directory not found or not a directory: {self.target_directory.name}"
            )
        elif not (self.file_path.exists() and self.file_path.is_file()):
            raise ValueError(f"File not found or not a file: {self.file_path}")

    @staticmethod
    def time_diff_str(last_modified: datetime) -> str:
        """Returns a string representing the time difference between the current time and the last modified time."""
        current_date = datetime.now()
        time_difference = current_date - last_modified
        hours = time_difference.total_seconds() // 3600

        if hours <= 72:
            return f"{int(hours)} hours ago"
        else:
            days = hours // 24
            return f"{int(days)} days ago"

    def get_last_modified(self) -> datetime:
        """Returns the last modified date and time of the file."""
        last_modified_timestamp: float = self.file_path.stat().st_mtime
        last_modified: datetime = datetime.fromtimestamp(
            last_modified_timestamp
        ).replace(second=0, microsecond=0)
        timedelta_str = self.time_diff_str(last_modified)
        print(f"- Time last modified: {last_modified} ({timedelta_str})")
        return last_modified

    def is_recent(self) -> bool:
        """Checks if the file was modified within the last 24 hours."""
        _24_hours_ago: datetime = datetime.now() - timedelta(hours=24)

        if _24_hours_ago <= self.get_last_modified():
            print("- Transfer not required.")
            return False
        return True

    def copy_file(self) -> None:
        """Copies the file to the target directory."""
        target_path = self.target_directory / self.file_path.name
        # shutil.copy2(self.file_path, target_path)
        print("- File transfer complete.")

    def remove_file(self) -> None:
        """Deletes the file."""
        # self.file_path.unlink()
        print(f"- File successfully deleted.")

    def process_file(self) -> None:
        """Processes the file by validating, transferring, and deleting (if required)."""
        print(self)
        sleep(1.5)
        try:
            self.validate_paths()
            if self.category == "award":
                self.copy_file()
                self.remove_file()
            elif not self.is_recent():
                self.copy_file()

        except Exception as e:
            print(f"- ERROR: {e}")
        print()


def get_award_files() -> Optional[list[FileTransfer]]:
    """Get local award files for transfer."""

    network_dir: Path
    local_dir: Path
    award_files: list[FileTransfer] = [
        FileTransfer(
            file_path=file_path, target_directory=network_dir, category="award"
        )
        for file_path in local_dir.iterdir()
        if not file_path.stem.startswith("$")
    ]
    if not award_files:
        print("No local award files found.\n")
    return award_files


def prepare_transfers() -> list[FileTransfer]:
    """Prepare file transfers by converting file paths and directories."""

    transfers: list[FileTransfer] = []
    for file_path, target_directory in transfers:
        transfers.append(
            FileTransfer(
                file_path=Path(file_path), target_directory=Path(target_directory)
            )
        )
    if award_files := get_award_files():
        transfers.extend(award_files)
    return transfers


def prepare_transfers():
    """Prepare file transfers by converting file paths and directories to FileTransfer object."""

    base_transfers: dict[str, str]

    transfers: list[FileTransfer] = []

    for file_path, target_dir in base_transfers.items():
        transfers.append(
            FileTransfer(file_path=Path(file_path), target_directory=Path(target_dir))
        )
    if local_award_files := get_award_files():
        transfers.extend(local_award_files)

    for file_transfer in transfers:
        yield file_transfer


def process_transfers():
    """Process file transfers."""

    with Console().status("Processing file transfers...") as status:
        for transfer in prepare_transfers():
            transfer.process_file()

    print("\nProcessing complete.\n")


if __name__ == "__main__":
    process_transfers()
