import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from typing import Optional

from rich.console import Console
from rich.traceback import install

install(show_locals=True)


@dataclass
class FileTransfer:
    file_path: Path
    target_dir: Path
    category: str = ""

    def __str__(self) -> str:
        self.category = self.category if self.category else None
        return (
            f"\n\n"
            f"file:             {self.file_path.name}\n"
            f"target_directory: {self.target_dir}\n"
            f"category:         {self.category}"
        )

    @staticmethod
    def _time_diff_str(last_modified: datetime) -> str:
        """
        Returns a string representing the time difference between the current time and the last modified time.
        """
        current_date = datetime.now()
        time_difference = current_date - last_modified
        hours = time_difference.total_seconds() // 3600

        if hours <= 72:
            duration = hours
            unit = "hours"
        else:
            duration = hours // 24
            unit = "days"
        return f"{duration} {unit} ago"

    def _get_last_modified(self) -> datetime:
        """
        Returns the last modified date and time of the file.
        """
        last_modified_timestamp: float = self.file_path.stat().st_mtime
        last_modified: datetime = datetime.fromtimestamp(
            last_modified_timestamp
        ).replace(second=0, microsecond=0)
        timedelta_str = self._time_diff_str(last_modified)
        print(f"- Time last modified: {last_modified} ({timedelta_str})")
        return last_modified

    def _is_recent(self) -> bool:
        """
        Checks if the file was modified within the last 24 hours.
        """
        _24_hours_ago: datetime = datetime.now() - timedelta(hours=24)

        if _24_hours_ago <= self._get_last_modified():
            return True
        print("- Transfer not required.")
        return False

    def _copy_file(self) -> None:
        """
        Copies the file to the target directory.
        """
        target_path = self.target_dir / self.file_path.name
        shutil.copy2(self.file_path, target_path)
        print("- File transfer complete.")

    def _remove_file(self) -> None:
        """
        Deletes the file.
        """
        self.file_path.unlink()
        print(f"- File successfully deleted.")

    def process_file(self) -> None:
        """
        Processes the file by validating, transferring, and deleting (if required).
        """
        print(self)
        sleep(1)
        try:
            if not (self.target_dir.exists() and self.target_dir.is_dir()):
                raise ValueError(
                    f"Directory not found or not a directory: {self.target_dir.name}"
                )
            elif not (self.file_path.exists() and self.file_path.is_file()):
                raise ValueError(f"File not found or not a file: {self.file_path}")
        
            if self.category == "award":
                self._get_last_modified()
                self._copy_file()
                self._remove_file()

            elif self._is_recent(): self._copy_file()
            # else: self.copy_file()
            

        except Exception as e:
            print(f"- ERROR: {e}")
        print()


def get_award_files() -> Optional[list[FileTransfer]]:
    """
    Get local award files for transfer.
    """

    network_dir: Path
    local_dir: Path
    award_files: list[FileTransfer] = [
        FileTransfer(file_path=file_path, target_dir=network_dir, category="award")
        for file_path in local_dir.iterdir()
        if not file_path.stem.startswith("$")
    ]
    if not award_files:
        print("No local award files found.\n")
    return award_files


def process_transfers():
    """
    * Prepare file transfers by converting file paths and directories to FileTransfer object.
    * Process file transfers
    """
    with Console().status(
        "[bright_yellow]Processing file transfers...[/bright_yellow]"
    ):
        parent_dir: Path
        base_transfers: tuple[tuple[Path, Path]]
        
        file_transfers: list[FileTransfer] = []
        
        for tranfser_pairs in base_transfers:
            for file_path, target_dir in tranfser_pairs:
                file_transfers.append(
                    FileTransfer(file_path=file_path, target_dir=target_dir)
                )
        if local_award_files := get_award_files():
            file_transfers.extend(local_award_files)

        for file_transfer in file_transfers:
            file_transfer.process_file()

    print("\nProcessing complete.\n")


# if __name__ == "__main__":
#     process_transfers()
