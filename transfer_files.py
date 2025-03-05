import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import NamedTuple


class TransferConfig(NamedTuple):
    file_path: str
    target_directory: str


def get_time_diff_string(last_modified: datetime) -> int:
    min_per_hour: int = 60
    sec_per_min: int = 60
    current_date = datetime.now()
    time_difference = current_date - last_modified
    hours = time_difference.total_seconds() // sec_per_min // min_per_hour
    if hours <= 72:
        value = hours
        time_unit = "hours"
    else:
        value = hours // 24
        time_unit = "days"
    value = str(int(value)).zfill(2)
    return f"{value} {time_unit} ago"


def get_time_last_modified(file_path: Path) -> datetime:
    last_modified_timestamp:float = os.path.getmtime(file_path)
    last_modified_datetime: datetime = datetime.fromtimestamp(last_modified_timestamp)
    return last_modified_datetime.replace(second=0, microsecond=0)


def is_update_within_last_day(time_last_modified: datetime) -> bool:
    one_day_ago: datetime = datetime.now() - timedelta(hours=24)
    return one_day_ago <= time_last_modified


def initiate_file_transfer(file_path: Path, target_directory: Path) -> None:
    if not (file_path.exists() and file_path.is_file()):
        raise ValueError(f"file not found or not a file: {file_path.name}")
    if not (target_directory.exists() and target_directory.is_dir()):
        raise ValueError(
            f"directory not found or not a directory: {target_directory.name}"
        )

    try:
        if not _testing:
            target_path = target_directory / file_path.name
            shutil.copy2(file_path, target_path)

    except Exception as e:
        print(f"Error: {file_path.name} - {e}")


def get_local_archived_award_files() -> list[TransferConfig]:
    network_archive_dir: Path
    local_archive_dir: Path
    awards_to_transfer: list[TransferConfig] = [
        TransferConfig(file_path=file_path, target_directory=network_archive_dir)
        for file_path in local_archive_dir.iterdir()
        if file_path.is_file()
    ]
    return awards_to_transfer


def remove_local_archived_award_files(
    transferred_award_files: list[TransferConfig],
) -> None:
    if _testing or not transferred_award_files:
        return
    for award in transferred_award_files:
        try:
            award.file_path.unlink()
            print(f"Successfully deleted {award.file_path.name}")
        except Exception as e:
            print(f"{award.file_path.name} - {e}")


def get_testing_mode_selection():
    available_modes = (True, False)
    print("Select the testing mode.")

    for _ in range(3):
        try:
            [print(f"{idx}: {value}") for idx, value in enumerate(available_modes)]
            user_selection = input(f">>> ").strip()
            return available_modes[int(user_selection)]
        except Exception:
            print("Invalid input. Please enter a number.")

    print("Unable to proceed with file transfers.")
    exit()


def main():
    print()
    try:
        txn_report = TransferConfig()
        sas_awards = TransferConfig()
        
        pending_transfers: list[TransferConfig] = [txn_report, sas_awards]
        awards_to_transfer: list[TransferConfig] = get_local_archived_award_files()
        if awards_to_transfer:
            pending_transfers.extend(awards_to_transfer)
        
        for pending in pending_transfers:
            time_last_modified: datetime = get_time_last_modified(pending.file_path)
            time_difference = get_time_diff_string(time_last_modified)
            
            if not is_update_within_last_day(time_last_modified):
                not_required_msg = "\n" + (
                    ">>> Transfer not required.\n"
                    f"    file: {pending.file_path.name}\n"
                    f"    last modified: {str(time_last_modified)[:-3]} "
                    f"({time_difference})"
                )
                print(not_required_msg)
                continue

            initiate_file_transfer(pending.file_path,pending.target_directory)
            transfer_message = "\n" + (
                ">>> Transfer complete.\n"
                f"    file: {pending.file_path.name}\n"
                f"    last modified: {str(time_last_modified)[:-3]} "
                f"({time_difference})"
            )
            print(transfer_message)
        remove_local_archived_award_files(awards_to_transfer)

    except Exception as e:
        print(f"### Error: {e}")


if __name__ == "__main__":
    _testing = get_testing_mode_selection()
    main()
