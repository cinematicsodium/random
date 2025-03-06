import win32com.client


def delete_login_verification_emails(subject_to_delete):
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)
    items_to_delete = [
        item for item in inbox.Items if subject_to_delete in item.Subject
    ]
    if not items_to_delete:
        print(f"No emails found that contain the subject '{subject_to_delete}'")
        return
    for item in items_to_delete:
        item.Delete()
    deleted_count = len(items_to_delete)
    print(f"Successfully deleted {deleted_count} messages with the subject '{subject_to_delete}'")
    outlook = None


if __name__ == "__main__":
    subject_to_delete = "Login PIN verification"
    delete_login_verification_emails(subject_to_delete)
