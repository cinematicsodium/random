from typing import Dict, Generator, List, Optional, Union
from datetime import datetime, time, timedelta
from pprint import pprint
from pathlib import Path
import shutil
import fitz #type: ignore
import json
import os



_testing_: bool = False
_example_: bool = False
_print_data_: bool = True
_write_xls_rows_: bool = True
_insert_date_: bool = True
_rename_move_file_: bool = True
_update_serial_numbers_: bool = True

if _example_:
    _insert_date_ = False
    _rename_move_file_ = False
    _update_serial_numbers_ = False

received_date_is_tomorrow: bool = False
current_time = datetime.now().time()
cutoff_time = time(14,45)
if current_time > cutoff_time:
    received_date_is_tomorrow = True

PROCESSING_FOLDER: str = (
    r"C:\processing"
)
FY24_FOLDER: str = (
    r"X:\fy24"
)
TEST_FOLDER: str = (
    r"C:\test"
)
AWARD_SER_NUMS: str = (
    r"process_award_data\serial_numbers.txt"
)

def validate_page_count(page_count: int) -> None:
    min_page_count, max_page_count = 2, 5
    if not (min_page_count <= page_count <= max_page_count):
        raise ValueError(f"Page Count: {page_count} (not in range {min_page_count}-{max_page_count})")

def validate_pay_plan(key: str, val: str) -> None:
    if key.startswith("pay plan") \
    and (
        val.startswith("es") \
        or \
        val.startswith("ses")
    ):
        raise ValueError(f"Error: Excepted Service Employee\nPay Plan: {val.upper()}")

def get_pdf_fields(pdf_file: str) -> dict:
    with fitz.open(pdf_file) as doc:
        min_page_count: int = 2
        max_page_count: int = 5
        page_count: int = doc.page_count
        first_page: int = 0
        last_page: int = page_count - 1
        pdf_fields: dict = {
            "first_page": {},
            "mid_pages": {},
            "last_page": {},
            "page_count": page_count,
            "file_name": os.path.basename(pdf_file)
        }
        field_count: int = 0

        if not (min_page_count <= page_count <= max_page_count):
            raise ValueError(f"Page Count: {page_count} (not in range {min_page_count}-{max_page_count})\n")
        elif page_count == 2:
            pdf_fields["category"] = "IND"
        else:
            pdf_fields["category"] = "GRP"

        for page in doc:
            current_page: int = page.number
            for field in page.widgets():
                key: str = field.field_name.strip().lower()
                val: str = field.field_value.strip()
                if all([
                    val == str(val),
                    not str(val).isspace(),
                    val != "",
                    str(val).lower() != "off",
                ]):
                    if current_page == first_page:
                        validate_pay_plan(key,val)
                        pdf_fields["first_page"][key] = val
                        field_count += 1
                    elif current_page == last_page:
                        pdf_fields["last_page"][key] = val
                        field_count += 1
                    elif first_page < current_page < last_page:
                        pdf_fields["mid_pages"][key] = val
                        field_count += 1

        if field_count <= 10:
            error_field_count: str = f"Insufficient number of PDF fields. Count: {field_count}"
            raise ValueError(error_field_count)
        return pdf_fields


def xjustification(field_text: str) -> str:
    justif_str: str = (
        field_text.strip()
        .encode("utf-8", errors="ignore")
        .decode("ascii", errors="ignore")
        .replace('"', "'")
        .replace("  "," ")
    )
    return '"' + justif_str + '"'


def xname(field_text: str) -> str:
    replacements: list[str] = ["Dr.","Mr.","Mrs.","Miss.","Ms."]
    for i in replacements:
        field_text.replace(i,"")
    last_first: str = ""
    if " " in field_text:
        split_name = field_text.split()
        for i in split_name:
            if "(" in i and ")" in i or (i[0] == '"' == i[-1]):
                split_name.remove(i)  # i == 'NickName' or (NickName)
        if len(split_name) == 2:
            if "," in split_name[0]:  # [0,1] = Last, First
                last_first = field_text
            elif (
                "." not in field_text
            ):  # [0,1] = First Last  -  not F. Last  -  not First L.
                last_first = ", ".join([split_name[1], split_name[0]])
        elif len(split_name) == 3:
                if all(
                    [
                        "," not in split_name[0],
                        1 <= len(split_name[1]) < 3,
                    ]
                ): # [0,1,2] = First M. Last  -  not F. M. Last  -  not First Middle Last
                    last_first = ", ".join([split_name[2], split_name[0]])
    return last_first.title() if last_first else field_text


def xnumerical(field_text: str) -> float:
    digits: str = "".join(i for i in field_text if any([i == ".", i.isdigit()]))
    if not digits:
        return 0
    return float(digits)


def ljust(text: str|int, int: int) -> str:
    return str(text).ljust(int)


def rjust(text: str|int, int: int) -> str:
    return str(text).rjust(int)


def get_nominator_name(first_page_fields: dict) -> str:
    for field_name, field_text in first_page_fields.items():
        if field_name in ["please print", "nominators name"]:
            return xname(field_text)
    return ""


def get_funding_org(first_page_fields: dict) -> str:
    pass


def get_type(first_page_fields: dict, grp=False, ind=False) -> str:
    if ind is True:
        sas_fields: list[str] = ['hours_2','time off award','special act or service','undefined',]
        for field_name in first_page_fields.keys():
            if field_name in sas_fields:
                return "SAS"
        return "OTS"
    elif grp is True:
        ots_fields: list[str] = ['on the spot','hours',]
        for field_name in first_page_fields.keys():
            if field_name in ots_fields:
                return "OTS"
        return "SAS"
    raise ValueError("Unable to determine the award type.")


def get_justification(last_page: dict) -> str:
    for field_name, field_text in last_page.items():
        if "extent" in field_name:
            return xjustification(field_text)
    raise ValueError("Award justification not found.")

def get_value_and_extent(last_page: dict) -> dict:
    value_choices: list[str] = ["moderate", "high", "exceptional"]
    extent_choices: list[str] = ["limited", "extended", "general"]
    value_extent_str_and_idx: dict = {}
    page_fields = list(last_page.items())

    for field_name, field_text in page_fields:
        if field_name in value_choices:
            value_extent_str_and_idx["Value"] = {
                "Text": field_name.capitalize(),
                "Index": value_choices.index(field_name),
            }
        elif field_name in extent_choices:
            value_extent_str_and_idx["Extent"] = {
                "Text": field_name.capitalize(),
                "Index": extent_choices.index(field_name),
            }
    if not value_extent_str_and_idx:
        for field_name, field_text in page_fields:
            if "extent" in field_name:
                justification_text: list = field_text.split(" ")
                for i in range(36, len(justification_text), 8):
                    n: int = i - 36
                    sentence: str = " ".join(justification_text[n:i])
                    val_ext_found: list[str] = []
                    for v in value_choices:
                        for e in extent_choices:
                            if v in sentence and e in sentence:
                                val_ext_found = [v,e]
                                break
                    if not val_ext_found:
                        return {}
                    else:
                        for text in val_ext_found:
                            sentence = sentence.replace(
                                text, "--- " + text.upper() + " ---"
                            )
                        val_ext_msg = (
f"""
=== Value and Extent Detection Results ===

Detected Value and Extent:
{val_ext_found}

Sentence:
>>> {sentence} <<<

---
1 = Accept
0 = Deny
"""
)
                        print(val_ext_msg)
                        choice: str = input(">>> ").strip()
                        if choice == "" or choice == "0":
                            return {}
                        elif choice == str(1):
                            xvalue,xextent = val_ext_found[0],val_ext_found[1]
                            value_extent_str_and_idx["Value"] = {
                                "Text": xvalue.capitalize(),
                                "Index": value_choices.index(xvalue),
                            }
                            value_extent_str_and_idx["Extent"] = {
                                "Text": xextent.capitalize(),
                                "Index": extent_choices.index(xextent),
                            }
    return value_extent_str_and_idx

def validate_award_amounts(
        nominees: Union[Dict,List[Dict]],
        value_extent_str_and_idx: dict,
        is_group: bool = False,
        is_individual: bool = False
) -> None:
    monetary_limits: list[list[int]] = [
        [500, 1000, 3000],      # moderate
        [1000, 3000, 6000],     # high
        [3000, 6000, 10000],    # exceptional
    ]   # limited | extended | general
    time_limits: list[list[int]] = [
        [9, 18, 27],    # moderate
        [18, 27, 36],   # high
        [27, 36, 40],   # exceptional
    ]  # limited | extended | general
    value_index: int = value_extent_str_and_idx["Value"]["Index"]
    extent_index: int = value_extent_str_and_idx["Extent"]["Index"]
    max_monetary: int = monetary_limits[value_index][extent_index]
    max_hours: int = time_limits[value_index][extent_index]

    total_monetary: int = 0
    total_hours: int = 0
    nominee_details: str = ""
    nap_policy: str = ""
    name_len: int = 0
    money_len: int = 0
    if is_group:
        total_monetary = sum(nominee["Monetary"] for nominee in nominees)
        total_hours = sum(nominee["Hours"] for nominee in nominees)
        name_len = max([len(nominee['Name'])for nominee in nominees]) + 4
        money_len = max([len(str(nominee['Monetary']))for nominee in nominees]) + 4
        nominee_details = "\n".join(
                f"- {nominee['Name'].ljust(name_len)}Monetary: ${str(nominee['Monetary']).ljust(money_len)}Hours: {nominee['Hours']}"
                for nominee in nominees
            )
        nap_policy = (
f"""
NAP 332.2 - page 11, attached
    - The total amount of a special act or service award to multiple employees is based on
      the value of the tangible and intangible benefits accruing from the contribution.
    - The total amount of the award may not exceed the amount that would be authorized
      if the contribution had been made by one individual.
"""
)
    elif is_individual and isinstance(nominees,dict):
        total_monetary = nominees["Monetary"]
        total_hours = nominees["Hours"]
        name_len = len(nominees["Name"]) + 4
        money_len = len(str(nominees["Monetary"])) + 4
        nominee_details = f"- {nominees['Name'].ljust(name_len)}Monetary: ${str(nominees['Monetary']).ljust(money_len)}Hours: {nominees['Hours']}"
        nap_policy = (
f"""
NAP 332.2 - page 22, attached
        Examples of combining award types:
        - A nomination for $250 and 4.30 hours of time-off meets the commensurate 100% total because
          $250 divided by $500 is 50%, and 50% of 9 hours is 4.30 hours.
        - A combined nomination for $250 and 8 hours would equate to too many hours to equal 100%.
        - In this scenario, either the monetary award or the time off hours would need to be adjusted
          to equal a combined 100%.
"""
)
    monetary_percentage = total_monetary / max_monetary
    time_percentage = total_hours / max_hours
    total_percentage = monetary_percentage + time_percentage
    total_len: int = max(
        [
            len(str(total_monetary))+4,
            len(str(total_hours))+4
        ]
    )
    if total_percentage > 1:
        valStr: str = value_extent_str_and_idx['Value']['Text']
        extStr: str = value_extent_str_and_idx['Extent']['Text']
        nominee_key: str = "Nominee:" if is_individual else "Nominees:"
        error_message = (
f"""
Error: Award amounts exceed the maximum allowed based on the selected award value and extent.

Award Details:
- Value:   {valStr}
- Extent:  {extStr}

{valStr} x {extStr} Limits: (NAP 332.2, Pg. 21 - 23)
- Monetary:  ${max_monetary}
- Time-Off:  {max_hours} hours

{nominee_key}
{nominee_details}

Monetary Total:   ${str(total_monetary).ljust(total_len)}{monetary_percentage:.2%} of limit.
Time-Off Total:    {str(total_hours).ljust(total_len)}{time_percentage:.2%} of limit.

Percentage Sum:   {total_percentage:.2%}
Max Allowed:      100%

{nap_policy}

Please make the appropriate corrections and resubmit for processing.

Thank you."""
)
        raise ValueError(error_message)


def get_shared_ind_grp_data(pdf_fields: dict) -> dict:
    first_page_fields: dict = pdf_fields["first_page"]
    last_page_fields: dict = pdf_fields["last_page"]
    shared_data: dict = {
        "Funding Org": get_funding_org(first_page_fields),
        "Nominator": get_nominator_name(first_page_fields),
        "Justification": get_justification(last_page_fields),
        "Type": (
            get_type(first_page_fields, grp=True)
            if pdf_fields["category"] == "GRP"
            else get_type(first_page_fields, ind=True)
        ),
    }
    if None in shared_data.values():
        none_fields = [
            str("- " + field)
            for field in shared_data.keys()
            if shared_data[field] is None
        ]
        none_fields_err = "\n".join(none_fields)
        raise Exception(f"Error:\nMissing required fields:\n{none_fields_err}\n")
    return shared_data


def writeXlsRows(award_data: dict) -> None:
    spreadsheet_rows_txt = r"C:\spreadsheet"
    award_id = award_data["Award ID"]
    award_date = award_data["Date Received"]
    award_category = award_data["Category"]
    award_type = award_data["Type"]
    award_nominator = award_data["Nominator"]
    award_org = award_data["Funding Org"]
    award_just = award_data["Justification"]
    if award_data.get("Nominee"):  # IND
        award_nominee = award_data["Nominee"]
        award_money = award_data['Monetary']
        award_time = award_data["Hours"]
        xls_row = f"{award_id}\t{award_date}\t\t{award_nominee}\t{award_category}\t{award_type}\t{award_money}\t{award_time}\t{award_nominator}\t{award_org}\t\t{award_just}\n"
        with open(spreadsheet_rows_txt, "a") as f:
            f.write(xls_row)
    elif award_data.get("Nominees"):  # GRP
        for nominee in award_data["Nominees"]:
            award_nominee = nominee["Name"]
            award_money = nominee["Monetary"]
            award_time = nominee["Hours"]
            xls_row = f"{award_id}\t{award_date}\t\t{award_nominee}\t{award_category}\t{award_type}\t{award_money}\t{award_time}\t{award_nominator}\t{award_org}\t\t{award_just}\n"
            with open(spreadsheet_rows_txt, "a") as f:
                f.write(xls_row)


def determine_date_received(pdf_fields: dict) -> str:
    date: str = ""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    for k, v in pdf_fields["first_page"].items():
        if k == "date received" and v.lower() != "today":
            return v
    if received_date_is_tomorrow:
        date = tomorrow.strftime("%Y-%m-%d")

    else:
        date = today.strftime("%Y-%m-%d")
    if not date:
        raise ValueError("Unable to determine date received.")
    return date

def insertDateReceived(filePath: str, award_data: dict) -> None:
    with fitz.open(filePath) as doc:
        for page in doc:
            for field in page.widgets():
                fkey: str = field.field_name.lower()
                fxrf: str = field.xref
                if fkey == "date received":
                    date = page.load_widget(fxrf)
                    date.field_value = award_data["Date Received"]
                    date.update()
                    doc.saveIncr()

def format_and_save(fileName: str, award_data: dict) -> str:
    formatted_data: dict = award_data.copy()
    k_len = max([len(k) for k in formatted_data.keys()])
    formatted_data["Justification"] = (
        str(len(formatted_data["Justification"].split())) + " words"
    )
    if formatted_data["Category"] == "IND":
        formatted_data["Monetary"] = "$" + str(formatted_data["Monetary"])
        formatted_data["Hours"] = str(formatted_data["Hours"]) + " hours"
        formatted_data["Nominee"] = (
            f"{formatted_data['Nominee']}    {formatted_data['Monetary']}    {formatted_data['Hours']}"
        )
        del formatted_data["Monetary"]
        del formatted_data["Hours"]
    elif formatted_data["Category"] == "GRP":
        nominees = formatted_data["Nominees"]
        formatted_data["Nominees"] = format_grp_nominees(nominees)
    res: str = (
        fileName
        + '\n\n'
        + "\n".join(f"{(k + ':').ljust(k_len + 2)} {v}" for k, v in formatted_data.items())
        + '\n'
        + "." * 50
        + '\n\n'
    )
    with open(r"process_award_data\awards_output.txt", "a") as f:
        f.write(res)
    return res
def createNewFileName(award_data: dict) -> str:
    id: str = award_data["Award ID"]
    org: str = award_data["Funding Org"]
    nominee: str = (
        award_data["Nominee"]
        if award_data.get("Nominee")
        else str(len(award_data["Nominees"])) + " nominees"
    )
    date: str = award_data["Date Received"]
    return " - ".join(
        [
            id,
            org,
            nominee,
            date,
        ]
    )


def create_new_file_path(original_path: Path, new_file_name: str) -> Path:
    return original_path.parent / f"{new_file_name}.pdf"

def validate_file_name(file_name: str) -> None:
    if not file_name.strip():
        raise ValueError("New file name cannot be empty.")
    if "/" in file_name or "\\" in file_name:
        raise ValueError("New file name cannot contain path separators.")

def renameAwardFile(file_path: str, new_file_name: str) -> Optional[Path]:
    try:
        validate_file_name(new_file_name)
        
        original_path = Path(file_path)
        new_path = create_new_file_path(original_path, new_file_name)
        
        original_path.rename(new_path)
        return new_path
    
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except PermissionError:
        print(f"Permission denied when renaming file: {file_path}")
    except ValueError as ve:
        print(f"Invalid file name: {ve}")
    except Exception as e:
        print(f"Error occurred while renaming file: {e}")
    return None


def determine_grp_configuration(page_count: int) -> list[list]:
    all_configs_nom_i1 = ("employee name_3", "award amount_2", "time off hours_2")
    all_configs_nom_i2 = ("employee name_4", "award amount_3", "time off hours_3")
    all_configs_nom_i3 = ("employee name_5", "award amount_4", "time off hours_4")
    all_configs_nom_i4 = ("employee name_6", "award amount_5", "time off hours_5")
    all_configs_nom_i5 = ("employee name_7", "award amount_6", "time off hours_6")
    all_configs_nom_i6 = ("employee name_8", "award amount_7", "time off hours_7")
    all_grp_configuration_duplicates: list = [
        all_configs_nom_i1,
        all_configs_nom_i2,
        all_configs_nom_i3,
        all_configs_nom_i4,
        all_configs_nom_i5,
        all_configs_nom_i6,
    ]

    nom_i7 = ("employee name_9", "award amount_8", "time off hours_8")
    nom_i8 = ("employee name_10", "award amount_9", "time off hours_9")
    nom_i9 = ("employee name_11", "award amount_10", "time off hours_10")
    nom_i10 = ("employee name_12", "award amount_11", "time off hours_11")
    nom_i11 = ("employee name_13", "award amount_12", "time off hours_12")
    nom_i12 = ("employee name_14", "award amount_13", "time off hours_13")
    nom_i13 = ("employee name_15", "award amount_14", "time off hours_14")
    max14_max21_duplicates: list = [
        nom_i7,
        nom_i8,
        nom_i9,
        nom_i10,
        nom_i11,
        nom_i12,
        nom_i13,
    ]

    max7_config: list = [
        ("employee name_2", "award amount", "time off hours")
    ] + all_grp_configuration_duplicates

    max14_config: list = max7_config + max14_max21_duplicates

    max21_config: list = (
        [("employee name_1", "award amount", "time off hours")]
        + all_grp_configuration_duplicates
        + max14_max21_duplicates
        + [("employee name_15", "award amount_15", "time off hours_15")]
        + [("employee name_16", "award amount_16", "time off hours_16")]
        + [("employee name_17", "award amount_10", "time off hours_10")]
        + max14_config[10:]
    )

    if page_count == 3:
        return max7_config
    elif page_count == 4:
        return max14_config
    elif page_count == 5:
        return max21_config
    return []


def get_grp_nominees_names_and_award_amounts(
    grp_nominees_fields: list[list], mid_page_fields: dict
) -> list[dict]:
    nominees_detected: list = []
    nominees_processed: list = []
    no_award_amounts_found: list = []

    for nominee_fields in grp_nominees_fields:
        nominee_name_field: str = nominee_fields[0]
        monetary_field: str = nominee_fields[1]
        hours_field: str = nominee_fields[2]
        current_nominee: dict = {"Name": None, "Monetary": 0, "Hours": 0}

        for field_name, field_text in mid_page_fields.items():
            if "left blank" in field_text.lower():
                continue
            field_text = xname(field_text)
            if "employee name" in field_name and (field_name,field_text) not in nominees_detected:
                nominees_detected.append((field_name,field_text))
            current_nominee["Name"] = (
                xname(field_text)
                if current_nominee["Name"] is None and field_name == nominee_name_field
                else current_nominee["Name"]
            )
            current_nominee["Monetary"] = (
                xnumerical(field_text)
                if field_name == monetary_field
                else current_nominee["Monetary"]
            )
            current_nominee["Hours"] = (
                xnumerical(field_text)
                if field_name == hours_field
                else current_nominee["Hours"]
            )

        if current_nominee["Name"] is not None:
            if current_nominee["Monetary"] == 0 and current_nominee["Hours"] == 0:
                if len(grp_nominees_fields) == 21 and nominee_fields in (
                    grp_nominees_fields[13],
                    grp_nominees_fields[14],
                ):
                    continue
                no_award_amounts_found.append(
                    ", ".join(f"{k}: {v}" for k, v in current_nominee.items())
                )
            nominees_processed.append(current_nominee)
    if len(nominees_detected) == 0:
        raise ValueError("No nominees detected.")
    elif len(nominees_processed) == 0:
        raise ValueError("Unable to process nominees.")
    elif len(nominees_detected) > len(nominees_processed):
        join_detected = "\n\t".join(str(i) for i in nominees_detected)
        join_processed = "\n\t".join(str(i) for i in nominees_processed)
        det_pro_err_0 = "Error:"
        det_pro_err_1 = (
            "Number of nominees detected does not match number of nominees processed\n"
        )
        det_pro_err_2 = f"Detected: {len(nominees_detected)}\n\t{join_detected}\n"
        det_pro_err_3 = f"Processed: {len(nominees_processed)}\n\t{join_processed}\n"
        det_pro_err_msg = (
            "\n".join(
                [
                    det_pro_err_0,
                    det_pro_err_1,
                    det_pro_err_2,
                    det_pro_err_3,
                ]
            )
            + "\n"
        )
        raise Exception(det_pro_err_msg)
    elif no_award_amounts_found:
        join_no_award = "\n\t".join(str(i) for i in no_award_amounts_found)
        raise Exception(f"Error: No award amounts found.\n\t{join_no_award}\n")
    return nominees_processed


def format_grp_nominees(nominees: list[dict]) -> str:
    max_name_len = max([len(nominee["Name"]) for nominee in nominees]) + 5
    max_monetary_len = max([len(str(nominee["Monetary"])) for nominee in nominees]) + 5
    return "\n    " + "\n    ".join(
        f"{(nominee['Name']+':').ljust(max_name_len)}${str(nominee['Monetary']).ljust(max_monetary_len)}{nominee['Hours']} hours"
        for nominee in nominees
    )


def process_grp_award_data(pdf_fields: dict, grp_sn: int) -> dict:
    last_page_fields: dict = pdf_fields["last_page"]
    mid_pages_fields = pdf_fields["mid_pages"]
    grp_award_data: dict = {
        "Award ID": "24-GRP-" + str(grp_sn).zfill(3),
    }
    shared_ind_grp_data: dict = get_shared_ind_grp_data(pdf_fields)
    grp_award_data.update(shared_ind_grp_data)
    grp_award_data["Category"] = "GRP"
    group_configuration = determine_grp_configuration(pdf_fields["page_count"])
    nominees = get_grp_nominees_names_and_award_amounts(group_configuration, mid_pages_fields)
    value_and_extent: dict = get_value_and_extent(last_page_fields)
    if value_and_extent:
        validate_award_amounts(nominees, value_and_extent, is_group=True)
        grp_award_data["Value"] = value_and_extent["Value"]["Text"]
        grp_award_data["Extent"] = value_and_extent["Extent"]["Text"]
    grp_award_data["Nominees"] = nominees
    grp_award_data["Date Received"] = determine_date_received(pdf_fields)
    return grp_award_data


def get_ind_name_amounts(first_page_fields: dict) -> dict:
    ind_name_amounts: dict = {
        "Name": None,
        "Monetary": 0,
        "Hours": 0,
    }
    for field_name, field_text in first_page_fields.items():
        if ind_name_amounts["Name"] is None and field_name == "employee name":
            ind_name_amounts["Name"] = xname(field_text)

        elif (
            ind_name_amounts["Monetary"] == 0
            and field_name in ["amount", "undefined"]
            or "the spot" in field_name
        ):
            ind_name_amounts["Monetary"] = xnumerical(field_text)

        elif ind_name_amounts["Hours"] == 0 and "hours" in field_name:
            ind_name_amounts["Hours"] = xnumerical(field_text)
    ind_name_amounts_str = "\t".join(f"{k}: {v}" for k, v in ind_name_amounts.items())
    if ind_name_amounts["Monetary"] == 0 == ind_name_amounts["Hours"]:
        raise Exception(f"No award amount found.\n{ind_name_amounts_str}\n")
    elif ind_name_amounts["Name"] is None:
        raise Exception("Unable to determine IND award nominee")
    return ind_name_amounts


def process_ind_award_data(pdf_fields: dict, ind_sn: int) -> dict:
    first_page_fields: dict = pdf_fields["first_page"]
    last_page_fields: dict = pdf_fields["last_page"]
    ind_award_data: dict = {
        "Award ID": "24-IND-" + str(ind_sn).zfill(3),
    }
    # if str(pdf_fields["file_name"]).startswith("24-"):
    #     ind_award_data["Award ID"] = pdf_fields["file_name"].split(" ")[0]
    shared_ind_grp_data: dict = get_shared_ind_grp_data(pdf_fields)
    ind_award_data.update(shared_ind_grp_data)
    ind_award_data["Category"] = "IND"
    nominee_name_award_amounts: dict = get_ind_name_amounts(first_page_fields)
    value_and_extent: dict = get_value_and_extent(last_page_fields)
    if value_and_extent:
        validate_award_amounts(nominee_name_award_amounts, value_and_extent, is_individual=True)
        ind_award_data["Value"] = value_and_extent["Value"]["Text"]
        ind_award_data["Extent"] = value_and_extent["Extent"]["Text"]
    ind_award_data["Nominee"] = nominee_name_award_amounts["Name"]
    ind_award_data["Monetary"] = nominee_name_award_amounts["Monetary"]
    ind_award_data["Hours"] = nominee_name_award_amounts["Hours"]
    ind_award_data["Date Received"] = determine_date_received(pdf_fields)
    if ind_award_data["Nominator"] == ind_award_data["Nominee"]:
        award_error: str = "\n".join(f"{k}: {v}" for k,v in ind_award_data.items())
        raise ValueError(f"Error: Nominator == Nominee\n\n{award_error}")
    return ind_award_data


def getSerialNums() -> dict:
    with open(AWARD_SER_NUMS, "r") as f:
        jsonSerNums = json.load(f)
        serialNums: dict[str,int] = {
            "IND": jsonSerNums["IND"],
            "GRP": jsonSerNums["GRP"],
        }
        return serialNums


def updateSerialNums(serialNums: dict) -> None:
    with open(AWARD_SER_NUMS, "w") as f:
        json.dump(serialNums, f, indent=4)


def move_file(filePath: str) -> None:
    shutil.move(filePath, FY24_FOLDER)


def processFiles(file_paths) -> None:
    serialNums: dict = getSerialNums()
    indID: int = serialNums["IND"]
    grpID: int = serialNums["GRP"]
    notProcessed: list[str] = []
    for file_path in file_paths:
        fileName: str = os.path.basename(file_path)
        if fileName.startswith("#"):
            continue
        try:
            pdfFields: dict = get_pdf_fields(file_path)
            awardCategory: str = pdfFields["category"]
            awardData: dict = {}
            formattedData: str = ""
            if awardCategory == "GRP":
                awardData = process_grp_award_data(pdfFields, grpID)
            else:
                awardData = process_ind_award_data(pdfFields, indID)
            if _write_xls_rows_:
                writeXlsRows(awardData)
            if _print_data_:
                formattedData = format_and_save(fileName,awardData)
                print(formattedData)
            if not _testing_:
                if _insert_date_:
                    insertDateReceived(str(file_path), awardData)
                newFileName: str = createNewFileName(awardData)
                if _rename_move_file_:
                    newFilePath = renameAwardFile(file_path, newFileName)
                    move_file(newFilePath)
            if awardCategory == "GRP" and str(grpID).zfill(3) in newFileName.split()[0]:
                grpID += 1
            elif awardCategory == "IND" and str(indID).zfill(3) in newFileName.split()[0]:
                indID += 1
        except Exception as e:
            hash_block: str = "#####\n"*5
            error_message = (
f"""
{hash_block}
{fileName}
{e}
{'.' * 50}
"""
)
            print(error_message)
            with open(r'process_award_data\awards_output.txt','a') as f:
                f.write(error_message+"\n")
            notProcessed.append(fileName)
    if _update_serial_numbers_ and not _testing_:
        updateSerialNums({"IND": indID, "GRP": grpID})
    if len(notProcessed) > 0:
        print(f"Not Processed ({len(notProcessed)}):")
        print("\n".join(notProcessed))


if __name__ == "__main__":
    print()
    print(" START ".center(100, "."))
    print()
    try:
        folderPath: str = PROCESSING_FOLDER if not _testing_ else TEST_FOLDER
        file_paths: Generator = Path(folderPath).rglob("*pdf")
        processFiles(file_paths=file_paths)
    except Exception as e:
        print(e)
    print()
    print(" END ".center(100, "."))
    if received_date_is_tomorrow:
        print('RECEIVED DATE == TOMORROW\n'*5)

