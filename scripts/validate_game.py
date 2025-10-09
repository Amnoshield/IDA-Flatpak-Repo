import os
import re
import requests
import textwrap

token = os.environ["GITHUB_TOKEN"]
repo = os.environ["GITHUB_REPOSITORY"]
issue_number = os.environ["ISSUE_NUMBER"]
issue_body = os.environ["ISSUE_BODY"]
issue_title = os.environ["ISSUE_TITLE"]

# ✅ Expected fields and regex rules
regex_rules = {
    "game_id": r"^[a-zA-Z0-9\._]+$",
    "file_name": r"^(?!([~/\\]))(?!.*(\.){2,})^[a-zA-Z0-9\._-]+$",
    "source_url": r"^https:\/\/github\.com\/[^\/]+\/[^\/]+\/releases\/download\/.+\.tar\.xz$",
    "sha256": r"^[A-Fa-f0-9]{64}$",
    "agreements": None,  # Checkbox
}

# ✅ Only validate issues matching this form type or title prefix
ALLOWED_TITLES = ["[New Game]:", "[Update Game]:"]


def api_request(method, url, **kwargs):
    headers = {"Authorization": f"token {token}"}
    return requests.request(method, url, headers=headers, **kwargs)


def comment_issue(message):
    api_request(
        "POST",
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
        json={"body": message},
    )


def close_issue():
    api_request(
        "PATCH",
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        json={"state": "closed"},
    )


def label_issue(label):
    api_request(
        "POST",
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels",
        json={"labels": [label]},
    )


def parse_issue_body(body):
    """Parse GitHub issue form body into key-value pairs."""
    if "### " not in body:
        return {}  # Not a form submission
    fields = {}
    key = None
    value = []
    for line in body.splitlines():
        if line.startswith("### "):
            if key and value:
                fields[key] = "\n".join(value).strip()
            key = line.replace("### ", "").strip()
            value = []
        elif key:
            value.append(line)
    if key and value:
        fields[key] = "\n".join(value).strip()
    return fields


def validate_fields(fields):
    errors = []
    for field, pattern in regex_rules.items():
        if field not in fields:
            errors.append(f"❌ Missing required field: **{field}**")
            continue

        value = fields[field].strip()
        if pattern is None:
            # Checkbox validation
            if "[x]" not in value.lower():
                errors.append(f"☑️ You must check at least one box in **{field}**.")
            continue

        if not re.match(pattern, value):
            errors.append(f"❌ **{field}** value '{value}' is invalid.")
    return errors


def main():
    # 🧩 1. Check allowed issue title/form type
    if not any(issue_title.startswith(t) for t in ALLOWED_TITLES):
        print("Issue not from an approved form — skipping validation.")
        return

    # 🧩 2. Parse issue form fields
    fields = parse_issue_body(issue_body)

    if not fields:
        comment_issue(
            "⚠️ This issue doesn’t appear to use the required issue form.\n"
            "Please use the proper issue template so we can process it correctly."
        )
        label_issue("invalid")
        close_issue()
        print("Non-form issue detected and closed.")
        exit(1)

    # 🧩 3. Validate fields
    errors = validate_fields(fields)

    if errors:
        message = "⚠️ **Issue validation failed**:\n" + "\n".join(errors)
        comment_issue(message)
        label_issue("invalid")
        close_issue()
        print("Validation failed and issue closed.")
        exit(1)

    # 🧩 4. Success
    comment_issue(textwrap.dedent("""
        ✅ **Issue validation passed successfully!**
        Awaiting environment approval to continue.
    """))
    print("Validation passed.")


if __name__ == "__main__":
    main()
import os
import re
import requests
import textwrap

# Environment from GitHub
token = os.environ["GITHUB_TOKEN"]
repo = os.environ["GITHUB_REPOSITORY"]
issue_number = os.environ["ISSUE_NUMBER"]
issue_body = os.environ["ISSUE_BODY"]
issue_title = os.environ["ISSUE_TITLE"]

# ✅ Expected fields and validation rules
regex_rules = {
    "Email": r"^[\w\.-]+@[\w\.-]+\.\w+$",
    "URL": r"^https?://[^\s]+$",
    "Version": r"^\d+\.\d+\.\d+$",
    "Steps to Reproduce": r".+",
}

# ✅ Checkbox fields (must all be checked)
checkbox_fields = [
    "Confirmations",
]

# ✅ Only run validation for issue forms with these title prefixes
ALLOWED_TITLES = ["[Bug]:", "[Feature Request]:"]


def api_request(method, url, **kwargs):
    headers = {"Authorization": f"token {token}"}
    return requests.request(method, url, headers=headers, **kwargs)


def comment_issue(message):
    api_request(
        "POST",
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
        json={"body": message},
    )


def close_issue():
    api_request(
        "PATCH",
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        json={"state": "closed"},
    )


def label_issue(label):
    api_request(
        "POST",
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels",
        json={"labels": [label]},
    )


def parse_issue_body(body):
    """Parse GitHub issue form body (### field headings and their values)."""
    if "### " not in body:
        return {}
    fields = {}
    key = None
    value = []
    for line in body.splitlines():
        if line.startswith("### "):
            if key and value:
                fields[key] = "\n".join(value).strip()
            key = line.replace("### ", "").strip()
            value = []
        elif key:
            value.append(line)
    if key and value:
        fields[key] = "\n".join(value).strip()
    return fields


def validate_text_fields(fields):
    """Validate standard input/text fields."""
    errors = []
    for field, pattern in regex_rules.items():
        if field not in fields:
            errors.append(f"❌ Missing required field: **{field}**")
            continue

        value = fields[field].strip()
        if not re.match(pattern, value):
            errors.append(f"❌ **{field}** value '{value}' is invalid.")
    return errors


def validate_checkboxes(fields):
    """Validate that all checkboxes are checked."""
    errors = []
    for field in checkbox_fields:
        if field not in fields:
            errors.append(f"❌ Missing required checkbox field: **{field}**")
            continue

        lines = [line.strip().lower() for line in fields[field].splitlines() if line.strip()]
        if not lines:
            errors.append(f"❌ **{field}** section is empty.")
            continue

        # Each checkbox line should look like "- [x] description"
        unchecked = [l for l in lines if not re.match(r"[-*]\s*\[x\]", l)]
        if unchecked:
            errors.append(
                f"☑️ All checkboxes in **{field}** must be checked. "
                f"The following are unchecked:\n- " + "\n- ".join(unchecked)
            )
    return errors


def main():
    # 🧩 1. Only run validation for approved form titles
    if not any(issue_title.startswith(t) for t in ALLOWED_TITLES):
        print("Issue not from an approved form — skipping validation.")
        return

    # 🧩 2. Parse issue body
    fields = parse_issue_body(issue_body)
    if not fields:
        comment_issue(
            "⚠️ This issue doesn’t appear to use the required issue form.\n"
            "Please open a new issue using the proper template."
        )
        label_issue("invalid")
        close_issue()
        print("Non-form issue detected and closed.")
        exit(1)

    # 🧩 3. Validate fields
    errors = validate_text_fields(fields) + validate_checkboxes(fields)

    if errors:
        message = "⚠️ **Issue validation failed**:\n" + "\n".join(errors)
        comment_issue(message)
        label_issue("invalid")
        close_issue()
        print("Validation failed and issue closed.")
        exit(1)

    # 🧩 4. Success
    comment_issue(textwrap.dedent("""
        ✅ **Issue validation passed successfully!**
        Awaiting environment approval to continue.
    """))
    print("Validation passed.")


if __name__ == "__main__":
    main()

