import csv
from pathlib import Path


ACCESS_CONTROL_FILE = Path("config/access_control.csv")


def load_access_control_rules():
    """
    Loads role and anonymized user access rules from a private CSV file.

    Expected CSV format:
    email,role,anonymized_user_id
    admin@example.com,admin,*
    user@example.com,user,user_1
    """

    admin_emails = set()
    user_email_to_anon_id = {}

    if not ACCESS_CONTROL_FILE.exists():
        raise FileNotFoundError(
            f"Access control file not found: {ACCESS_CONTROL_FILE}"
        )

    with ACCESS_CONTROL_FILE.open(mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            email = row["email"].strip().lower()
            role = row["role"].strip().lower()
            anonymized_user_id = row["anonymized_user_id"].strip()

            if role == "admin":
                admin_emails.add(email)

            elif role == "user":
                user_email_to_anon_id[email] = anonymized_user_id

    return admin_emails, user_email_to_anon_id