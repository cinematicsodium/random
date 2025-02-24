import os
import shutil
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class TransferConfig:
    file_path: str
    target_directory: str


def round_to_hour(dt: datetime) -> datetime:
    if dt.minute >= 30:
        return (dt + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    else:
        return dt.replace(minute=0, second=0, microsecond=0)


def get_time_last_modified(file_path: str) -> datetime:
    last_modified_timestamp:float = os.path.getmtime(file_path)
    last_modified_datetime: datetime = datetime.fromtimestamp(last_modified_timestamp)
    last_modified_rounded: datetime = round_to_hour(last_modified_datetime)
    return last_modified_rounded


def is_update_within_last_day(time_last_modified: datetime) -> bool:
    one_day_ago: datetime = datetime.now() - timedelta(hours=24)
    return one_day_ago <= time_last_modified


def initiate_file_transfer(file_path: str, target_directory: str) -> None:
    file_name: str = os.path.basename(file_path)
    directory_name: str = os.path.basename(target_directory)

    if not os.path.exists(file_path):
        raise ValueError(f"file not found: {file_name}")
    elif not os.path.isfile(file_path):
        raise ValueError(f"path is not a file: {file_name}")
    elif not os.path.exists(target_directory):
        raise ValueError(f"directory not found: {directory_name}")
    elif not os.path.isdir(target_directory):
        raise ValueError(f"path is not a directory: {directory_name}")

    target_path: str = os.path.join(target_directory, file_name)
    shutil.copy2(file_path, target_path)
    print(f"> file transfer complete: {file_name}")


def main():
    print()
    try:
        txn_report = TransferConfig()
        sas_awards = TransferConfig()
        
        pending_transfers: list[TransferConfig] = [txn_report, sas_awards]
        
        padding: int = max(len(os.path.basename(pending.file_path)) for pending in pending_transfers) + 4
        
        for pending in pending_transfers:
            file_name: str = os.path.basename(pending.file_path)
            time_last_modified: datetime = get_time_last_modified(pending.file_path)
            
            if not is_update_within_last_day(time_last_modified):
                print(
                    f"### Transfer not required - "
                    f"file: {file_name.ljust(padding)}"
                    f"last modified: {str(time_last_modified)[:-3]}"
                )
                continue
            
            if TESTING:
                print(f"> file transfer complete: {pending.file_path}")
                continue

            initiate_file_transfer(pending.file_path,pending.target_directory)

    except Exception as e:
        print(f"### Error: {e}")

TESTING = True
if __name__ == "__main__":
    main()
