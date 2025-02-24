import os
import win32com.client

class NameFormatter:
    @staticmethod
    def _split_name(raw_name: str) -> list[str]:
        return raw_name.split() if " " in raw_name else [raw_name]

    @staticmethod
    def _format_last_name(last_name: str) -> str:
        chars = list(last_name)
        if "'" in last_name:
            apostrophe_idx = chars.index("'")
            if 1 <= apostrophe_idx <= 2:
                chars[apostrophe_idx + 1] = chars[apostrophe_idx + 1].upper()
        elif last_name.lower().startswith("mc"):
            chars[2] = chars[2].upper()
        return "".join(chars)

    @staticmethod
    def _standardize_name_parts(name_parts: list[str] | str) -> tuple[str, str]:
        last_name, first_name = "", ""
        if isinstance(name_parts, list):
            if name_parts[0].endswith(","):
                last_name, first_name = name_parts[0][:-1], name_parts[1]
            elif "," in name_parts[0]:
                last_name, first_name = name_parts[0].split(",")
            else:
                first_name, last_name = name_parts[0], name_parts[1]
        elif isinstance(name_parts, str):
            if "," in name_parts:
                last_name, first_name = name_parts.split(",")

        uppercase_count = sum(c.isupper() for c in last_name + first_name)
        if not (2 <= uppercase_count <= 5):
            last_name, first_name = (
                NameFormatter._format_last_name(last_name.capitalize()),
                first_name.capitalize(),
            )

        return last_name, first_name

    @staticmethod
    def format_name(raw_name: str) -> str:
        if not raw_name:
            raise ValueError("Name field is blank.")
        name_parts = NameFormatter._split_name(raw_name)
        last_name, first_name = NameFormatter._standardize_name_parts(name_parts)
        return ", ".join([last_name, first_name])


def rename_file(file_path: str, supervisor_name: str, employee_name: str) -> str:
    directory = os.path.dirname(file_path)
    new_name = f"Audit _ DEI Compliance _ {supervisor_name} _ {employee_name}.msg"
    new_path = os.path.join(directory, new_name)
    os.rename(file_path, new_path)
    return new_name


def get_employee_name(email_body: str) -> str:
    cleaned_body = email_body.replace("\n", " ").replace("\r", " ")
    words = [x.strip() for x in cleaned_body.split() if x.strip()]
    name_parts = [part for part in words[55:60] if part.lower() not in ["for", "below", "must", "be"]]
    cleaned_name_parts = ["".join(c for c in part if c.isalpha()) for part in name_parts]
    return " ".join(cleaned_name_parts).replace(".", "")

def get_supervisor_and_employee_names(file_path: str) -> list[str]:
    outlook = win32com.client.Dispatch('Outlook.Application').GetNamespace('MAPI')
    msg = outlook.OpenSharedItem(file_path)
    employee_name = get_employee_name(msg.Body)
    supervisor_name = msg.To
    if "@" in supervisor_name:
        supervisor_name = supervisor_name.split("@")[0].title()
    cleaned_supervisor_name = supervisor_name.replace(".", " ").replace("'", "").strip()
    del outlook, msg
    return [NameFormatter.format_name(i) for i in [cleaned_supervisor_name, employee_name]]

def process_files(files: list[str]) -> None:
    for file in files:
        if "For Action_" in file:
            file_name = file.split("For Action_")[1].strip()
        else:
            file_name = os.path.basename(file)
        print(f"File: {file_name}")
        try:
            supervisor_name, employee_name = get_supervisor_and_employee_names(file)
            rename_file(file, supervisor_name, employee_name)
        except Exception as e:
            print(e)
