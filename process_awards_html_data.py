from datetime import datetime, timedelta
from time import sleep

from bs4 import BeautifulSoup


def get_html_content() -> str:
    file: str = "html_data_dump.html"
    with open(file, "r") as f:
        html_content: str = f.read()
        sections: list[str] = [
            section.strip() for section in html_content.split("<tr>") if section.strip()
        ]
        cleaned_content: str = "\n".join(
            line.strip()
            for section in sections
            for line in section.split("\n")
            if line.strip()
        )
    with open(file, "w") as f:
        pass
    return cleaned_content


def extract_text_from_html(html_content: str) -> list[str]:
    soup = BeautifulSoup(html_content, "html.parser")
    return [line.strip() for line in soup.get_text().split("\n") if line.strip()]


def parse_award_items(cleaned_content: list[str]):
    award_items: list[tuple[str, ...]] = []
    for i, line in enumerate(cleaned_content):
        if i + 5 >= len(cleaned_content):
            continue
        if any(line.startswith(code) for code in []):
            noa_code: int = int(cleaned_content[i][:3])
            award_date: datetime = datetime.strptime(cleaned_content[i + 1], "%m/%d/%Y")
            award_value: int = int(
                float(
                    "".join(
                        char
                        for char in cleaned_content[i + 5]
                        if char.isdigit() or char == "."
                    )
                )
            )
            award_items.append((noa_code, award_date, award_value))
    return award_items


def is_within_one_year(award_date: datetime) -> bool:
    today: datetime = datetime.now()
    one_year_ago: datetime = today - timedelta(days=365)
    return one_year_ago <= award_date <= today


def filter_by_date(extracted_info: list[tuple]) -> list[tuple]:
    date_filtered_items: list[tuple] = [
        extracted for extracted in extracted_info if is_within_one_year(extracted[1])
    ]
    return date_filtered_items


def format_award_items(date_filtered_items: list[tuple]) -> str:
    code_map: dict[int, str] = {
        000: {"category": "000"},
    }
    header: str = f'[Count: {len(date_filtered_items)}] ...\n'
    string: str = ""
    for item in date_filtered_items:
        noa_code, item_date, amount = item
        category: str = code_map[noa_code]["category"]
        amount: str = f"${amount}" if noa_code in (000, 000) else f"{amount} hrs."
        string += f">>> {item_date.date()}, NOA {noa_code}, {category}, {amount}\n"
    return '"' + (header + string).strip() + '"'


def save_to_file(string: str) -> None:
    with open("file.txt", "w") as file:
        file.write(string)
        print(string)
        print(f"{datetime.now().replace(microsecond=0)}...saved to file.\n")


def fetch_and_log_daily_awards():
    while True:
        print(datetime.now().replace(microsecond=0))
        raw_html_content = get_html_content()
        if raw_html_content:
            plain_text_award_data = extract_text_from_html(raw_html_content)
            award_details = parse_award_items(plain_text_award_data)
            if not award_details:
                print("[count: 0]")
                continue
            recent_award_items = filter_by_date(award_details)
            formatted_items_string = format_award_items(recent_award_items)
            save_to_file(formatted_items_string)
        sleep(2)
