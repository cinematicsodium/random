import json

import fitz

PDF_PATH: str
JSON_PATH: str


def extract_org_codes_and_symbols_from_pdf(file_path: str = PDF_PATH) -> list[str]:
    with fitz.open(file_path) as pdf_document:
        extracted_text_data = [
            line.strip()
            for page in pdf_document
            for line in str(page.get_text()).split("\n")
        ]
        return extracted_text_data


def validate_org_details(primary_code: str, secondary_code: str, org_title) -> bool:
    return all([org_title != "", len(primary_code) == 10, len(secondary_code) == 10])


def extract_org_details_from_default_format(
    extracted_text_data: list[str],
) -> dict | None:
    try:
        org_symbol = extracted_text_data[0]
        primary_code, *org_title = extracted_text_data[1].split(" ", 1)
        org_title = " ".join(org_title)
        secondary_code = extracted_text_data[2].split(" ")[0]
        return {
            "primary_code": primary_code,
            "symbol": org_symbol,
            "title": org_title,
            "secondary_code": secondary_code,
        }
    except IndexError as e:
        print(f"Insufficient data for extraction (default format): {e}")
        return None


def extract_org_info_from_alternate_format(
    extracted_text_data: list[str],
) -> dict | None:
    try:
        primary_code = extracted_text_data[0]
        org_title = extracted_text_data[1]
        org_symbol = extracted_text_data[2]
        secondary_code = extracted_text_data[3]
        return {
            "primary_code": primary_code,
            "symbol": org_symbol,
            "title": org_title,
            "secondary_code": secondary_code,
        }
    except IndexError as e:
        print(f"Insufficient data for extraction (alternate format): {e}")
        return None


def collect_valid_org_info(extracted_text_data: list[str]) -> list[dict]:
    if not extracted_text_data:
        raise ValueError("No text provided.")

    valid_org_details = []
    for block_index in range(0, len(extracted_text_data) - 4):
        block = extracted_text_data[block_index : block_index + 4]

        for extractor in [
            extract_org_details_from_default_format,
            extract_org_info_from_alternate_format,
        ]:
            org_details = extractor(block)
            is_valid_org = validate_org_details(
                org_details["primary_code"],
                org_details["secondary_code"],
                org_details["title"],
            )
            if org_details and is_valid_org:
                valid_org_details.append(
                    {
                        "symbol": org_details["symbol"],
                        "code": org_details["primary_code"],
                        "title": org_details["title"],
                    }
                )
                break
    return valid_org_details


def save_as_json(org_details: list[dict]) -> None:
    with open(JSON_PATH, "w") as yfile:
        json.dump(org_details, yfile, indent=4, sort_keys=True)
        print("saved org info to file.")


def extract_and_save_org_data():
    try:
        extracted_text_data = extract_org_codes_and_symbols_from_pdf()
        org_details = collect_valid_org_info(extracted_text_data)
        save_as_json(org_details)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    extract_and_save_org_data()
