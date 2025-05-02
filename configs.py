from dataclasses import dataclass
from types import NoneType

from awards.configs import BaseDetails, EmployeeDetails


@dataclass
class GroupAward(BaseDetails):
    def __post_init__(self):
        super().__post_init__()

        self.employees: list[EmployeeDetails] = []

    def export_json(self):
        source_path = self.source_path.name if self.source_path else None
        justification = (
            f"{len(self.justification.split(' '))} words"
            if isinstance(self.justification, str)
            else None
        )
        emp_dict: dict[str,EmployeeDetails] = {}
        none_count: int = 0
        for employee in self.employees:
            if not employee.name:
                emp_dict[f"_None_{none_count+1}"] = employee
            else:
                emp_dict[employee.name] = employee
        sorted_names = sorted(list(emp_dict.keys()))
        sorted_employees = {idx+1:emp_dict[sorted_name].as_dict() for idx,sorted_name in enumerate(sorted_names)}
        attributes: dict[str, str | int | None | list[EmployeeDetails]] = {
            "source_path": source_path,
            "log_id": self.log_id,
            "funding_org": self.funding_org,
            "funding_string": self.funding_string,
            "nominator_name": self.nominator_name,
            "nominator_org": self.nominator_org,
            "approver_name": self.approver_name,
            "approver_org": self.approver_org,
            "certifier_name": self.certifier_name,
            "certifier_org": self.certifier_org,
            "value": self.value,
            "extent": self.extent,
            "justification": justification,
            "category": self.category,
            "type": self.type,
            "date_received": self.date_received,
            "consultant": self.consultant,
            "employees": sorted_employees,
        }
        for k, v in attributes.items():
            if type(v) not in [dict, float, int, list, NoneType, str]:
                v = str(v)
                attributes[k] = v
        return attributes

##############################################################################################################################################################################

import warnings
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import fitz

from awards.constants import CONSULTANT_MAP, EvalManager
from awards.formatting import Formatter
from awards.logger import Logger
from awards.utils import IDManager, find_mgmt_division

logger = Logger()
formatter = Formatter()


@dataclass
class BaseDetails:
    source_path: Optional[Path | str] = None

    def __post_init__(self):
        self.log_id: Optional[str] = None
        self.funding_org: Optional[str] = None
        self.nominator_name: Optional[str] = None
        self.nominator_org: Optional[str] = None
        self.funding_string: Optional[str] = None
        self.certifier_name: Optional[str] = None
        self.certifier_org: Optional[str] = None
        self.approver_name: Optional[str] = None
        self.approver_org: Optional[str] = None
        self.mb_division: Optional[str] = None
        self.justification: Optional[str] = None
        self.value: Optional[str] = None
        self.extent: Optional[str] = None
        self.category: Optional[str] = None
        self.type: Optional[str] = None
        self.date_received = datetime.now().strftime("%Y-%m-%d")
        self.consultant: Optional[str] = None
        self.pdf_data: dict[str, str] = {}
        self.validate_source_path()

    def validate_source_path(self) -> None:
        if self.source_path is None:
            return
        elif isinstance(self.source_path, str):
            self.source_path = Path(self.source_path.replace('"', "").strip())

        if not isinstance(self.source_path, Path):
            raise ValueError(
                f"Invalid source path type.  |  Expected: [Path, str, None]  |  Received: {type(self.source_path)}"
            )
        if not self.source_path.is_file() or not self.source_path.exists():
            raise ValueError(
                f"Source path '{self.source_path}' is not a file or does not exist."
            )

    def extract_pdf_data(self) -> dict[str, Optional[str]]:
        warnings.filterwarnings("ignore", module="pymupdf")
        with fitz.open(self.source_path) as doc:
            if doc.page_count == 2:
                self.category = "IND"
            elif doc.page_count in [3, 4, 5]:
                self.category = "GRP"
            else:
                raise ValueError(
                    f"Invalid page count. Expected: [2, 3, 4, 5]  |  Received: {doc.page_count}"
                )
            self.log_id = IDManager.get(self.category)
            for page in doc:
                for field in page.widgets():
                    key = formatter.key(field.field_name)
                    val = formatter.clean(field.field_value)
                    self.pdf_data[key] = val

        if not self.pdf_data:
            raise ValueError("No data extracted from the PDF.")
        warnings.resetwarnings()
        logger.info(f"Extracted {len(self.pdf_data)} items from PDF.")

    def get_first_match(self, *keys: str) -> Optional[str]:
        for key in keys:
            if key in self.pdf_data:
                return self.pdf_data[key]
        return None

    def set_value(self):
        value_options: list[str] = [
            field_name
            for field_name, field_value in self.pdf_data.items()
            if str(field_name).lower() in EvalManager.value_options
            and str(field_value).lower() == "on"
        ]
        self.value = value_options[0] if len(value_options) == 1 else None

    def set_extent(self):
        extent_options: list[str] = [
            field_name
            for field_name, field_value in self.pdf_data.items()
            if str(field_name).lower() in EvalManager.extent_options
            and str(field_value).lower() == "on"
        ]
        self.extent = extent_options[0] if len(extent_options) == 1 else None

    def set_funding_organization(self) -> None:
        # CODE BASED ON NOMINATOR ORG +
        self.set_consultant()

    def _set_mb_division(self, mb_orgs: list[str]) -> None:
        mb_div_list = []
        for org in mb_orgs:
            div_match = find_mgmt_division(org)
            mb_div_list.append(div_match) if div_match else None

        if mb_div_list:
            self.mb_division = Counter(mb_div_list).most_common()[0][0]

            if not self.mb_division:
                logger.warning(
                    f"Unable to determine MB orgs based on the following: {mb_orgs}"
                )
            else:
                logger.info(f"MB division set to '{self.mb_division}'")

    def set_consultant(self) -> None:
        """Set the consultant based on the funding organization."""
        self.consultant = CONSULTANT_MAP.get(self.funding_org)
        if self.consultant is None:
            logger.warning(f"No consultant found for funding org '{self.funding_org}'")
        logger.info("Consultant set for funding organization.")

##############################################################################################################################################################################

import re
from dataclasses import dataclass
from typing import Optional

from awards.formatting import Formatter

formatter = Formatter()


@dataclass(order=True)
class EmployeeDetails:
    _name: Optional[str] = None
    org: Optional[str] = None
    pay_plan: Optional[str] = None
    _supervisor_name: Optional[str] = None
    monetary_amount: Optional[int] = None
    time_off_amount: Optional[int] = None

    def __post_init__(self):
        self._name = formatter.name(self._name)
        self.supervisor_name = formatter.name(self.supervisor_name)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "pay_plan" and isinstance(self.pay_plan, str):
            self.__validate_pay_plan()

    def __str__(self):
        return str(self.as_dict())
    
    def as_dict(self) -> dict[str,int|str|None]:
        return {
            "Name": self.name,
            "Org": self.org,
            "Pay Plan": self.pay_plan,
            "Supervisor Name": self.supervisor_name,
            "Monetary Amount": self.monetary_amount,
            "Time-Off Amount": self.time_off_amount,
        }

    def __validate_pay_plan(self) -> None:
        if "es" in self.pay_plan.lower():
            pay_plan = re.sub("es", "*ES*", self.pay_plan, flags=re.IGNORECASE)
            raise ValueError(f"Pay plan: '{pay_plan}'  | 'ES' pay plans not allowed.")

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = formatter.name(value)

    @property
    def supervisor_name(self):
        return self._supervisor_name

    @supervisor_name.setter
    def supervisor_name(self, value):
        self._supervisor_name = formatter.name(value)


print(EmployeeDetails())
