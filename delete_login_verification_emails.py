import win32com.client


def delete_login_verification_emails(subject_to_delete):
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)
    items_to_delete = [
        item for item in inbox.Items if item.Subject == subject_to_delete
    ]
    if not items_to_delete:
        print(f"No emails found that contain the subject '{subject_to_delete}'")
        return
    for item in items_to_delete:
        item.Delete()
        print(f"Deleted email with subject: {subject_to_delete}")
    outlook = None


if __name__ == "__main__":
    subject_to_delete = "PAMS Login PIN verification"
    delete_login_verification_emails(subject_to_delete)
