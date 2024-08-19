from typing import Any, Dict, Generator, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import shutil
from webbrowser import get
from click import group
import fitz  # type: ignore
import json
import os

from matplotlib import category
from networkx import number_strongly_connected_components

@dataclass
class PDFData():
    first_page_fields: Dict[str, str] = field(default_factory=dict)
    mid_page_fields: Dict[str, str] = field(default_factory=dict)
    last_page_fields: Dict[str, str] = field(default_factory=dict)
    page_count: int = 0
    category: str = ""
    filename: str = ""

@dataclass
class StringAndIndex():
    text: str = ""
    index: int = 0

@dataclass
class AwardDetails():
    date: str = ""
    type: str = ""
    nominator: str = ""
    org: str = ""
    justification: str = ""
    value: StringAndIndex = field(default_factory=StringAndIndex)
    extent: StringAndIndex = field(default_factory=StringAndIndex)

@dataclass
class NomineeDetails():
    name: str = ""
    money: int = 0
    hours: int = 0

@dataclass
class IndividualAward(AwardDetails):
    id: str = ""
    category: str = "IND"
    nominee: NomineeDetails = field(default_factory=NomineeDetails)

@dataclass
class GroupAward(AwardDetails):
    category:  str = "GRP"
    nominees: List[NomineeDetails] = field(default_factory=list)

@dataclass
class SerialNumber():
    individual: int
    group: int

class TextFormat():
    title_prefixes: list[str] = ["Dr.", "Mr.", "Mrs.", "Miss.", "Ms.", "Prof.", "Rev.", "Hon.", "Sir", "Lady", "Capt.", "Col.", "Maj.", "Gen.", "Adm."]

    @staticmethod
    def justification(text: str) -> str:
        cleaned_text = (
            text.strip()
            .encode("utf-8", errors="ignore")
            .decode("ascii", errors="ignore")
            .replace('"', "'")
            .replace("  ", " ")
        )
        return f'"{cleaned_text}"'

    @staticmethod
    def name(name: str) -> str:
        name = name.strip()
        for prefix in TextFormat.title_prefixes:
            name = name.replace(prefix, "")

        split_name = [part for part in name.split(" ") \
            if not (part.startswith('(') and part.endswith(')') \
            or (part.startswith('"') and part.endswith('"')))
        ]

        if len(split_name) == 2:
            if "," in split_name[0]:
                return name.title()
            elif "." not in name:
                return f"{split_name[1]}, {split_name[0]}".title()
        elif len(split_name) == 3 and "," not in split_name[0] and 1 <= len(split_name[1]) < 3:
            return f"{split_name[2]}, {split_name[0]}".title()

        return name.title()

    @staticmethod
    def numerical(text: str) -> int:
        numeric_str = ''.join(char for char in text if char.isdigit() or char == '.')
        numeric_int: int
        try:
            numeric_int = int(numeric_str)
        except ValueError:
            raise ValueError(f"Invalid numerical value: {text}")
        return numeric_int

def get_pdf_data(file: str) -> PDFData:
    
    def validate_page_count(page_count: int) -> None:
        min_page_count, max_page_count = 2, 5
        if page_count not in range(min_page_count, max_page_count + 1):
            raise ValueError(f"Page count {page_count} is not within the valid range of {min_page_count}-{max_page_count}")

    def is_valid_field_value(value: str) -> bool:
        return all([
            value == str(value),
            not value.isspace(),
            value != "",
            value.lower() != "off",
        ])
    
    pdf_info = PDFData()
    with fitz.open(file) as doc:
        page_count: int = doc.page_count
        validate_page_count(page_count)
        first_page: int = 0
        last_page: int = page_count - 1
        pdf_info.page_count = page_count
        pdf_info.filename = os.path.basename(file)

        field_count: int = 0
        for page in doc:
            page_num: int = page.number
            fields = page.widgets()
            for field in fields:
                field_name: str = field.field_name.strip().lower()
                field_value: str = field.field_value.strip()

                if is_valid_field_value(field_value):
                    field_count += 1
                    if page_num == first_page:
                        pdf_info.first_page_fields[field_name] = field_value
                    elif page_num == last_page:
                        pdf_info.last_page_fields[field_name] = field_value
                    else:
                        pdf_info.mid_page_fields[field_name] = field_value

        if field_count <= 10:
            raise ValueError(f"Insufficient number of PDF fields. Count: {field_count}")

    return pdf_info

def get_serial_number() -> SerialNumber:
    file: str = "serial_numbers.json"
    with json.loads(open(file, "r").read()) as json_file:
        return SerialNumber(
            individual=json_file["IND"],
            group=json_file["GRP"],
        )

def determine_received_date(first_page_fields: dict) -> str:
    for k, v in first_page_fields["first_page"].items():
        if k == "date received" and v.lower() != "today":
            return v
    return datetime.now().strftime("%Y-%m-%d")

def determine_award_type(first_page_fields: dict, grp=False, ind=False) -> str:
    type: str = ""
    sas_fields: list[str] = ['hours_2','time off award','special act or service','undefined',]
    ots_fields: list[str] = ['on the spot','hours',]
    for field_name in first_page_fields.keys():
        if field_name in sas_fields:
            type = "SAS"
            break
        elif field_name in ots_fields:
            type = "OTS"
            break
    if not type:
        raise ValueError("Unable to determine the award type.")
    return type

def get_nominator_name(first_page_fields: dict) -> str:
    nominator: str = ""
    for field_name, field_text in first_page_fields.items():
        if field_name in ["please print", "nominators name"]:
            nominator = TextFormat.name(field_text)
            break
    if not nominator:
        raise ValueError("Nominator name not found.")
    return nominator

def get_funding_org(first_page_fields: dict) -> str:
    
    def collect_divisions(first_page_fields: dict) -> list[str]:
        divisions: list[str] = []
        for field_name, field_value in first_page_fields.items():
            if field_name.lower() in ("org_2", "organization_2"):
                continue
            if field_name.lower().startswith(("org_", "organization_")):
                divisions.append(field_value.upper())
        if not divisions:
            raise ValueError("Org divisions not found.")
        return divisions

    def define_funding_org(division_fields: list[str]) -> str:
        funding_org: str = ""
        aaa: list[str] = ['aaa-000', 'aaa-111', 'aaa-222', 'aaa-333', 'aaa-444']
        bbb: list[str] = ['bbb-000', 'bbb-111', 'bbb-222', 'bbb-333', 'bbb-444']
        ccc: list[str] = ['ccc-000', 'ccc-111', 'ccc-222', 'ccc-333', 'ccc-444']
        ddd: list[str] = ['ddd-000', 'ddd-111', 'ddd-222', 'ddd-333', 'ddd-444']
        eee: list[str] = ['eee-000', 'eee-111', 'eee-222', 'eee-333', 'eee-444']
        orgs: list[str] = [aaa, bbb, ccc, ddd, eee]
        for org in orgs:
            main_org: str = org[0]
            for div in org:
                for division_field in division_fields:
                    if div in division_field:
                        if main_org == "aaa-000":
                            funding_org = div
                        else:
                            funding_org = main_org
                        break
        return funding_org

    division_fields: list[str] = collect_divisions(first_page_fields)
    funding_org: str = define_funding_org(division_fields)

    if funding_org:
        return funding_org
    else:
        funding_orgs: list[str] = ['aaa', 'bbb', 'ccc', 'ddd', 'eee']
        divisions: str = "\n".join(f"- {i}" for i in division_fields)
        orgs: str = "\n".join(f"{i}: {org}" for i,org in enumerate(funding_orgs))
        funding_org_error_msg: str = f"""The following divisions could not be associated with a funding organization:\n{divisions}"""
        print(funding_org_error_msg)
        while True:
            print(f"Please select a funding organization from the following list:\n{orgs}")
            user_input: str = input(">>> ").strip()
            if user_input == "":
                raise ValueError("Unable to determine funding organization.")
            try:
                funding_org = funding_orgs[int(user_input)]
                break
            except ValueError:
                print(f"Invalid input.")
            except IndexError:
                print(f"Invalid input.")
    return funding_org

def get_award_justification(last_page: dict) -> str:
    for field_name, field_text in last_page.items():
        if "extent" in field_name:
            return TextFormat.justification(field_text)
    raise ValueError("Award justification not found.")

def get_award_value(last_page_fields: dict) -> StringAndIndex:
    value: StringAndIndex = StringAndIndex()
    value_choices: list[str] = ["moderate", "high", "exceptional"]
    for field_name, field_text in last_page_fields.items():
        if field_name in value_choices:
            value = StringAndIndex(
                text=field_text,
                index=field_text.index(field_text)
            )
    return value

def get_award_extent(last_page_fields: dict) -> StringAndIndex:
    extent: StringAndIndex = StringAndIndex()
    extent_choices: list[str] = ["limited", "extended", "general"]
    for field_name, field_text in last_page_fields.items():
        if field_name in extent_choices:
            extent = StringAndIndex(
                text=field_text,
                index=field_text.index(field_text)
            )
    return extent

def process_award_details(PDFData: PDFData) -> AwardDetails:
    award_details = AwardDetails(
        date=determine_received_date(PDFData.first_page_fields),
        type=determine_award_type(PDFData.first_page_fields),
        nominator=get_nominator_name(PDFData.first_page_fields),
        org=get_funding_org(PDFData.first_page_fields),
        justification=get_award_justification(PDFData.last_page_fields),
    )
    award_value: StringAndIndex = get_award_value(PDFData.last_page_fields)
    award_extent: StringAndIndex = get_award_extent(PDFData.last_page_fields)
    if award_value.text and award_extent.text:
        award_details.value = award_value
        award_details.extent = award_extent
    return award_details

def validate_award_amounts(NomineeDetails: NomineeDetails) -> None:
    if NomineeDetails.money == 0 and NomineeDetails.hours == 0:
        raise ValueError(f"{NomineeDetails}\nBoth nominee amount and hours are zero. At least one should have a non-zero value.")

def get_individual_nominee_details(PDFData: PDFData) -> NomineeDetails:
    
    def get_individual_name(first_page_fields: dict) -> str:
        name: str = ""
        for field_name, field_text in first_page_fields.items():
            if "employee name" in field_name:
                name = TextFormat.name(field_text)
                break
        if not name:
            raise ValueError("Nominee name not found.")
        return name
    
    def get_individual_money(first_page_fields: dict) -> int:
        money: int = 0
        monetary_fields: list[str] = ["amount", "undefined", "the spot"]
        for field_name, field_text in first_page_fields.items():
            for monetary_field in monetary_fields:
                if monetary_field in field_name:
                    money = TextFormat.numerical(field_text)
                    break
        return money
    
    def get_individual_hours(first_page_fields: dict) -> int:
        hours: int = 0
        for field_name, field_text in first_page_fields.items():
            if "hours" in field_name:
                hours = TextFormat.numerical(field_text)
                break
        return hours
    
    individual_nominee_details: NomineeDetails = NomineeDetails(
        name=get_individual_name(PDFData.first_page_fields),
        money=get_individual_money(PDFData.first_page_fields),
        hours=get_individual_hours(PDFData.first_page_fields),
    )
    validate_award_amounts(individual_nominee_details)
    return individual_nominee_details

def process_individual_award(file_path: str, serial_number: int) -> IndividualAward:
    pdf_content: PDFData = get_pdf_data(file_path)
    award_details: AwardDetails = process_award_details(PDFData)
    individual_nominee_details: NomineeDetails = get_individual_nominee_details(PDFData)
    individual_award = IndividualAward(
        award_details=award_details,
        individual_nominee_details=individual_nominee_details,
        id="24-IND-" + str(serial_number),
    )
    return individual_award

def enforce_award_limits(processed_indGrp_award) -> None:
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
    
    value_index: int = award.value.index
    extent_index: int = award.extent.index
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
        money_len = max([len(nominee['Monetary'])for nominee in nominees]) + 4
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
        ).strip()
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
        ).strip()
    monetary_percentage = total_monetary / max_monetary
    time_percentage = total_hours / max_hours
    total_percentage = monetary_percentage + time_percentage
    if total_percentage > 1:
        nominee_key: str = "Nominee:" if is_individual else "Nominees:"
        error_message = (
f"""
Error: Award amounts exceed the maximum allowed based on the selected award value and extent.

Award Details:
- Value:   {value_extent_str_and_idx['Value']['Text']}
- Extent:  {value_extent_str_and_idx['Extent']['Text']}

Limits:
- Monetary:  ${max_monetary}
- Time-Off:  {max_hours} hours

{nominee_key}
{nominee_details}

Total Monetary:   ${str(total_monetary).ljust(money_len)}{monetary_percentage:.2%} of limit.
Time-Off Total:    {str(total_hours).ljust(money_len)}{time_percentage:.2%} of limit.

Percentage Sum:   {total_percentage:.2%}
Max Allowed:      100%

{nap_policy}

Please make the appropriate corrections and resubmit for processing.

Thank you."""
)
        raise ValueError(error_message)

def writeXlsRows(award_data: dict) -> None:
    spreadsheet_rows_txt = r"C:\Users\joseph.strong\OneDrive - US Department of Energy\Python\process_award_data\spreadsheet_rows.txt"
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


def renameAwardFile(filePath: str, new_file_name: str) -> str:
    new_path: str = ""
    try:
        directory: str = os.path.dirname(filePath) + "\\"
        old_file_name: str = os.path.basename(filePath)
        new_path = directory + new_file_name + ".pdf"
        os.rename(filePath, new_path)
    except FileNotFoundError:
        print(f"{filePath} not found.")
    except Exception as e:
        print(f"Error occurred while renaming file: {e}")
    return new_path


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
            if "employee name" in field_name and field_text not in nominees_detected:
                nominees_detected.append(field_text)
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
    if str(pdf_fields["file_name"]).startswith("24-"):
        grp_award_data["Award ID"] = pdf_fields["file_name"].split(" ")[0]
    shared_ind_grp_data: dict = process_award_details(pdf_fields)
    grp_award_data.update(shared_ind_grp_data)
    grp_award_data["Category"] = "GRP"
    group_configuration = determine_grp_configuration(pdf_fields["page_count"])
    nominees = get_grp_nominees_names_and_award_amounts(
        group_configuration, mid_pages_fields
    )
    value_and_extent: dict = get_award_value(last_page_fields)
    if value_and_extent:
        enforce_award_limits(nominees, value_and_extent, is_group=True)
        grp_award_data["Value"] = value_and_extent["Value"]["Text"]
        grp_award_data["Extent"] = value_and_extent["Extent"]["Text"]
    grp_award_data["Nominees"] = nominees
    grp_award_data["Date Received"] = determine_received_date(pdf_fields)
    return grp_award_data




def process_ind_award_data(pdf_fields: dict, ind_sn: int) -> dict:
    first_page_fields: dict = pdf_fields["first_page"]
    last_page_fields: dict = pdf_fields["last_page"]
    ind_award_data: dict = {
        "Award ID": "24-IND-" + str(ind_sn).zfill(3),
    }
    if str(pdf_fields["file_name"]).startswith("24-"):
        ind_award_data["Award ID"] = pdf_fields["file_name"].split(" ")[0]
    shared_ind_grp_data: dict = process_award_details(pdf_fields)
    ind_award_data.update(shared_ind_grp_data)
    ind_award_data["Category"] = "IND"
    nominee_name_award_amounts: dict = get_ind_name_amounts(first_page_fields)
    value_and_extent: dict = get_award_value(last_page_fields)
    if value_and_extent:
        enforce_award_limits(nominee_name_award_amounts, value_and_extent, is_individual=True)
        ind_award_data["Value"] = value_and_extent["Value"]["Text"]
        ind_award_data["Extent"] = value_and_extent["Extent"]["Text"]
    ind_award_data["Nominee"] = nominee_name_award_amounts["Name"]
    ind_award_data["Monetary"] = nominee_name_award_amounts["Monetary"]
    ind_award_data["Hours"] = nominee_name_award_amounts["Hours"]
    ind_award_data["Date Received"] = determine_received_date(pdf_fields)
    return ind_award_data

def getSerialNums(file: int) -> None:
    with open(file, "r") as f:
        jsonSerNums = json.load(f)
        serialNums: dict[str,int] = {
            "IND": jsonSerNums["IND"],
            "GRP": jsonSerNums["GRP"],
        }
        return serialNums

def updateSerialNums(file: str, serialNums: dict) -> None:
    with open(file, "w") as f:
        json.dump(serialNums, f, indent=4)


def move_file(filePath: str) -> None:
    shutil.move(filePath, FY24_FOLDER)


def processFiles() -> None:
    try:
        serialNums: dict = getSerialNums()
        indID: int = serialNums["IND"]
        grpID: int = serialNums["GRP"]
        notProcessed: list[str] = []
        folderPath: str = PROCESSING_FOLDER if not TESTING else TEST_FOLDER
        file_paths: Generator = Path(folderPath).rglob("*pdf")
        for file_path in file_paths:
            fileName: str = os.path.basename(file_path)
            nameLen: int = len(fileName)
            try:
                pdfFields: dict = get_pdf_fields(file_path)
                awardCategory: str = pdfFields["category"]
                awardData: dict = {}
                formattedData: str = ""
                if awardCategory == "GRP":
                    awardData = process_grp_award_data(pdfFields, grpID)
                else:
                    awardData = process_ind_award_data(pdfFields, indID)
                if CREATE_XLS_ROWS:
                    writeXlsRows(awardData)
                if PRINT_AWARD_DATA:
                    formattedData = format_and_save(fileName,awardData)
                    print(formattedData)
                if not TESTING:
                    if INSERT_DATE:
                        insertDateReceived(str(file_path), awardData)
                    newFileName: str = createNewFileName(awardData)
                    if RENAME_AND_MOVE:
                        newFilePath: str = renameAwardFile(file_path, newFileName)
                        move_file(newFilePath)
                if awardCategory == "GRP":
                    grpID += 1
                else:
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
).strip()
                print(error_message)
                with open(r'process_award_data\awards_output.txt','a') as f:
                    f.write(error_message+"\n")
                notProcessed.append(fileName)
        if UPDATE_AWARD_SER_NUMS and not TESTING:
            updateSerialNums({"IND": indID, "GRP": grpID})
        if len(notProcessed) > 0:
            print(f"Not Processed ({len(notProcessed)}):")
            print("\n".join(notProcessed))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":

    print()
    print(" START ".center(100, "."))
    print()
    try:
        processFiles()
    except Exception as e:
        print(e)
    print()
    print(" END ".center(100, "."))
