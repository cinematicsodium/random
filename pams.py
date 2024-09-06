from datetime import datetime, timedelta
from dataclasses import dataclass
from writer import *

CURRENT_FY: str = "2024"
NEXT_FY: str = "2025"
PAMS_LINK: str = r"https://link.com"


@dataclass
class NewPlan():
    beginDate: str = ""
    endDate: str = "2025-09-30"
    reviewingOfficial: str = ""
    supervisor: str = ""
    noa: str = ""
    org: str = ""
    planType: str = ""


@dataclass
class PriorPlan():
    supervisor: str = ""
    reviewingOfficial: str = ""
    beginDate: str = ""
    endDate: str = ""
    planType: str = ""
    org: str = ""


def convert_date(date_str):
    current_year = datetime.now().year
    default_datetime_year = 1900
    date_formats = [
        "%m/%d",    # "01/01"
        "%m/%d/%Y", # "1/1/2000"
        "%m/%d/%y", # "1/1/00"
        "%Y-%m-%d", # "2000-01-01"
    ]
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, date_format)
            if parsed_date.year == default_datetime_year:
                parsed_date = parsed_date.replace(year=current_year)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"\nDate string '{date_str}' is not in a recognized format.")


def subtract_one_day(end_date):
    date = datetime.strptime(end_date, "%Y-%m-%d")
    new_date = date - timedelta(days=1)
    return new_date.strftime("%Y-%m-%d")


def select_org(prior:bool=False) -> str:
    naOrgs: list[str]=[
        'DOE','NA-1','NA-10','NA-15 (OST)','NA-20','NA-30','NA-40','NA-70','NA-80','NA-90','NA-CI','NA-COMM','NA-ESH','NA-GC','NA-IM','NA-KC (KCFO)','NA-LA (LAFO)','NA-LL (LFO)','NA-MB','NA-NV (NFO)','NA-PAS','NA-PFO','NA-SN (SFO)','NA-SV (SRFO)','NA-YFO']
    for idx,org in enumerate(naOrgs):
        print(idx,org,sep=": ")
    while True:
        text = "prior org" if prior else "org"
        print(f"\nSelect {text}:")
        try:
            org_idx = int(input(">>> ").strip())
            selected_org = naOrgs[int(org_idx)]
            return selected_org
        except Exception:
            print("\nInvalid input.")


def select_temporary_role() -> str:
    temporary_roles: list[str] = [
        "promotion",
        "excepted service appointment",
        "other",
    ]
    manual_temp_role_entry: int = len(temporary_roles) - 1
    
    while True:
        try:
            print("\nSelect a temporary role by entering the corresponding number:")
            for index, plan in enumerate(temporary_roles):
                print(f"{index}: {plan}")
            
            user_input: str = input(">>> ").strip()

            selected_idx = int(user_input)
            if selected_idx is not manual_temp_role_entry:
                return temporary_roles[selected_idx]
            else:
                print("\nEnter a temporary role:")
                user_input = input(">>> ").strip()
                return user_input
        except Exception:
            print("\nInvaid input.")


def select_plan_type(str:str) -> str:
    plan_types = [
        "SES Null",
        "Annual",
        "Annual (Terminated Employee)",
        "Annual (New Employee)",
        "Annual (New POR)",
        "Detail",
        "Temporary Position",
        "Advisory"
    ]
    while True:
        try:
            print(f"\nSelect the {str} plan type:")
            for index, plan in enumerate(plan_types):
                print(f"{index}: {plan}")
            
            user_input = input(">>> ").strip()

            selected_idx = int(user_input)
            return plan_types[selected_idx]

        except (ValueError, IndexError):
            print("\nInvalid input.")


def select_noa() -> str:
    internal_role_change_reasons: list[str] = [
        "career-conditional appointment",
        "conversion to a career SES appointment",
        "conversion to an excepted service appointment",
        "excepted service appointment",
        "new hire",
        "reassignment",
        "reinstatement-career conditional",
        "promotion",
        "temporary promotion",
        "transfer",
        "other",
    ]
    manual_entry_index: int = len(internal_role_change_reasons) - 1
    
    while True:
        try:
            print("\nSelect the appropriate internal role change:")
            for index,reason in enumerate(internal_role_change_reasons):
                print(f"{index}: {reason}")
            
            user_choice: str = input(">>> ").strip()
            
            if int(user_choice) == manual_entry_index:
                hire_reason = input("Enter the internal role change:\n>>> ").strip()
            else:
                hire_reason = internal_role_change_reasons[int(user_choice)]
            
            article_prefix: str = "an " if hire_reason and hire_reason[0].lower() in ['a', 'e', 'i', 'o', 'u'] else "a "
            return article_prefix + hire_reason.lower()
        
        except Exception as e:
            print(f"\nInvalid input.")


def create_internal_role_change() -> None:
    _employee_: str = input("\nemployee name: ").strip().title()
    _org_ = select_org()

    nature_of_action: str = select_noa()
    
    new = NewPlan(
        beginDate= convert_date(input("\nnew plan begin date: ").strip()),
        supervisor=input(f"\nnew plan supervisor: ").strip().title(),
        planType=select_plan_type("new"),
        org=_org_
    )
    
    prior = PriorPlan(
        supervisor=input("\nEnter prior plan supervisor (1=same as new plan supervisor): ").strip().title(),
        beginDate=convert_date(input("\nEnter prior plan begin date: ").strip()),
        endDate=subtract_one_day(new.beginDate),
        planType=select_plan_type("prior"),
        org=select_org(prior=True)
    )    
    if prior.supervisor == "1":
        prior.supervisor = new.supervisor
    
    reminder = f"REMINDER: PRIOR PAY POOL ({prior.org}) != NEW PAY POOL ({new.org})" if new.org != prior.org else ""
    
    internal_role_change_email: str = (
f"""PAMS _ {_org_} _ {_employee_.split(' ')[1]} _ {new.supervisor.split(' ')[1]} _ New Performance Plan
Hello,

A record has been added to the Performance Appraisal Management System (PAMS) for {_employee_}, supervised by {new.supervisor}, for {nature_of_action} effective {new.beginDate}.


New Plan:
A new performance plan must be established within 30 days of an employee starting a new position. 
This plan, which outlines job expectations and goals, must be electronically signed by both the employee and their supervisor to certify its implementation. 
It will be converted to the FY {NEXT_FY} Annual performance plan on {CURRENT_FY}-10-01. SPOs for this plan entered within the dates covered will be retained for FY {NEXT_FY}.
- Appraisal: {new.planType}
- Begin Date: {new.beginDate}
- End Date: {new.endDate}
- Supervisor: {new.supervisor}

Prior Plan:
This is the annual plan that the employee will be rated on at the end of FY {CURRENT_FY} based on work experience from {prior.beginDate} to {prior.endDate}.
- Appraisal: {prior.planType}
- Begin Date: {prior.beginDate}
- End Date: {prior.endDate}
- Supervisor: {prior.supervisor}

The link to PAMS is {PAMS_LINK}. To login, enter your email address and password. 
If you have forgotten your password, select Reset Password and a temporary password will be sent to you.


If you have questions or need assistance, please let me know.

{reminder}
"""
).strip()
    writer.write(internal_role_change_email)
    return


def create_new_hire() -> None:
    _employee_: str = input("\nemployee name: ").strip().title()
    _org_ = select_org()
    new_hire_reason: str = select_noa()
    new = NewPlan(
        supervisor=input(f"\nnew plan supervisor: ").strip().title(),
        beginDate=convert_date(input("\nnew plan begin date: ").strip()),
        planType=select_plan_type("new"),
    )

    new_hire_text: str = (
f"""PAMS _ {_org_} _ {_employee_.split(' ')[1]} _ {new.supervisor.split(' ')[1]} _ New Performance Plan
Hello,

A record has been added to the Performance Appraisal Management System (PAMS) for {_employee_}, supervised by {new.supervisor}, for {new_hire_reason} effective {new.beginDate}.

New Plan:
A new performance plan must be established within 30 days of an employee starting a new position. 
This plan, which outlines job expectations and goals, must be electronically signed by both the employee and their supervisor to certify its implementation. 
It will be converted to the FY {NEXT_FY} Annual performance plan on {CURRENT_FY}-10-01. SPOs for this plan entered within the dates covered will be retained for FY {NEXT_FY}.
- Appraisal: {new.planType}
- Begin Date: {new.beginDate}
- End Date: {new.endDate}
- Supervisor: {new.supervisor}

The link to PAMS is {PAMS_LINK}. To login, enter your email address and password. 
If you have forgotten your password, select Reset Password and a temporary password will be sent to you.

Please let me know if you have any questions.
"""
).strip()
    writer.write(new_hire_text)


def create_temporary_role() -> None:
    _employee_: str = input("\nemployee name: ").strip().title()
    _org_ = select_org()
    new = NewPlan(
        supervisor=input(f"\nnew plan supervisor: ").strip().title(),
        planType=select_plan_type("new"),
        noa=input("\nnature of action (1=detail, 2=temporary promotion): ").strip(),
        beginDate=convert_date(input("\nnew plan begin date: ").strip()),
        endDate=convert_date(input("\nnew plan end date: ").strip()),
    )
    _noa_ = "detail" if new.noa == "1" else "temporary promotion"
    
    
    email_text: str = (
f"""PAMS _ {_org_} _ {_employee_.split(' ')[1]} _ {new.supervisor.split(' ')[1]} _ New {_noa_.title()} Performance Plan
Hello,

A Detail performance plan has been added to the Performance Appraisal Management System (PAMS) for {_employee_}, supervised by {new.supervisor}, for a {_noa_} effective {new.beginDate} through {new.endDate}.

New {_noa_} plan:
Employees in a temporary role require a separate performance plan and assessment. Once the temporary role has been completed, the plan will be converted to "Advisory" status for the supervisor of record to reference. The Company Performance Policy states that the new performance plan should be established and certified (electronically signed by both) no later than 30 days from the effective date.
- Appraisal: {new.planType}
- Begin Date: {new.beginDate}
- End Date: {new.endDate}
- Supervisor: {new.supervisor}

The link to PAMS is {PAMS_LINK}. To login, enter your email address and password. 
If you have forgotten your password, select Reset Password and a temporary password will be sent to you.

If you have any questions, just let me know.
"""
).strip()
    writer.write(email_text)


if __name__ == "__main__":
    actions: list = [
        "new hire",
        "temporary role",
        "internal role change",
    ]
    while True:
        try:
            print("\nSelect an action to perform:")
            for index, action in enumerate(actions):
                print(f"{index}: {action}")

            user_input = input(">>> ").strip()

            selected_index = int(user_input)

            if selected_index not in [0,1,2]:
                print("\nInvalid selection. Please choose a valid option.")
                continue
            elif selected_index == 0:
                create_new_hire()
            elif selected_index == 1:
                create_temporary_role()
            elif selected_index == 2:
                create_internal_role_change()
            print("\n" + " New record created ".center(100,"."))
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
