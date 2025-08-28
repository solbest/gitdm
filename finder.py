import logging
import requests
import pandas as pd
import re
import time
import sys
from datetime import datetime, date, timedelta

# ---------------- CONFIG ------------------
GITHUB_TOKEN = "git token there"  # Replace with your GitHub token




ORG_KEYWORDS = [
    "inc", "corp", "llc", "labs", "group", "studio", "solution", "messenger",
    "repo", "project", "company", "service", "organization", 
    "bot", "guard", "system", "deploy", "team", "auto", "admin"
]

BAD_PATTERNS = [
    "info@", "support@", "admin@", "contact@", "team@", "no-reply@", "sales@",
    "bot", "automated", "notifications@", "example.com"
]

EMAIL_PATTERN = r"[^@]+@[^@]+\.[^@]+"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Load emails into a set once (do this at the beginning of your program)
def load_email_set(filepath):
    with open(filepath, 'r',encoding="utf-8") as file:
        emails = {line.strip().lower() for line in file if line.strip()}
    return emails

# Create a global email set (only once)
EMAIL_SET = load_email_set("scan_email_list.log")

# Function to check if an email exists
def email_exists(email: str) -> bool:
    return email.strip().lower() in EMAIL_SET

# ---------------- HELPERS ------------------
def is_personal_email(email: str) -> bool:
    if not email:
        return False
    email = email.lower()
    return bool(re.fullmatch(EMAIL_PATTERN, email)) and not any(pat in email for pat in BAD_PATTERNS)

def is_personal_username(username: str) -> bool:
    if not username:
        return False
    return not any(keyword in username.lower() for keyword in ORG_KEYWORDS)

def parse_args():
    if len(sys.argv) < 4:
        print("Usage: script.py <country> <max_followers> <max_repos> [startdate] [enddate] [startPage]")
        sys.exit(1)

    country = sys.argv[1]
    max_followers = int(sys.argv[2])
    max_repos = int(sys.argv[3]) 
    arg_suffix = ""
    start_page = 1
    start_date = ""
    end_date = ""

    if len(sys.argv) >= 6:
        start_date = sys.argv[4]
        end_date = sys.argv[5]
        arg_suffix = f"({start_date}~{end_date})"
        if len(sys.argv) == 7:
            try:
                start_page = int(sys.argv[6])
            except ValueError:
                print("Invalid start page number")
                sys.exit(1)
    elif len(sys.argv) == 5:
        try:
            start_page = int(sys.argv[4]) 
        except ValueError:
            start_date = sys.argv[4]
            end_date = str(date.today())
            arg_suffix = f"({start_date}~)"

    return country, max_followers, max_repos, start_date, end_date, start_page, arg_suffix

def setup_logging(log_file: str):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s\t%(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

# ---------------- MAIN LOGIC ------------------
def scan_users(country, max_followers, max_repos, start_date, end_date, start_page, log_suffix):
    alldetectcnt = totalcnt = cnt = 0
    date_filter = ""
    if log_suffix != "":
        date_filter = f"created:{start_date}..{end_date}+"

    result = "Success for all users."

    for page in range(start_page, 21): 
        query = f"https://api.github.com/search/users?q={date_filter}location:{country}+followers:<{max_followers}+repos:<{max_repos}&sort=joined&order=desc&per_page=50&page={page}"

        response = requests.get(query, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error fetching users: {response.status_code} - {response.text}")
            break

        data = response.json()
        if totalcnt == 0:
            totalcnt = data.get("total_count", 0)
            if totalcnt > 1000:
                print(f"Overflow: {totalcnt} results. GitHub only allows access to the first 1000.")
    
                # We need to get the last page (page 20, 50 users per page), and get the last user's joined date
                final_page_url = f"https://api.github.com/search/users?q={date_filter}location:{country}+followers:<{max_followers}+repos:<{max_repos}&sort=joined&order=asc&per_page=50&page=20"
                final_response = requests.get(final_page_url, headers=HEADERS)
                if final_response.status_code == 200:
                    final_items = final_response.json().get("items", [])
                    if final_items:
                        last_user_url = final_items[-1]["url"]
                        last_user_data = requests.get(last_user_url, headers=HEADERS).json()
                        raw_joined_date = last_user_data.get("created_at", "")
                        if raw_joined_date:
                            try:
                                parsed_date = datetime.strptime(raw_joined_date, "%Y-%m-%dT%H:%M:%SZ")
                                end_date = parsed_date.strftime("%Y-%m-%d")
                                next_date = parsed_date + timedelta(days=1)
                                result = "You need to scan more from " + next_date.strftime("%Y-%m-%d")
                                if log_suffix == "":
                                    log_suffix = f"(~{end_date})"
                                else:
                                    log_suffix = f"({start_date}~{end_date})"
                            except ValueError:
                                result = "You need to scan more!" 
                                print("last user data error")
                        else:
                            print("last user error")
                    else:
                        print("Could not retrieve users from final page.")
                else:
                    print(f"Error retrieving final page: {final_response.status_code} - {final_response.text}")

            if totalcnt == 0:
                sys.exit(0)

            totalcnt = min(totalcnt, 1000)
            choice = input(f"Do you scan these {totalcnt} users - {log_suffix}? (y/n): ").strip().lower()
            if choice != "y":
                sys.exit(0)

            log_file = f"{country}.{max_followers}.{max_repos}{log_suffix}.log"
            setup_logging(log_file)

            print(f"Scanning {totalcnt} users from {country} (starting at page {page})")

        detectcnt = 0
        for index, user in enumerate(data.get("items", []), 1):
            username = user["login"]
            profile_url = user["url"]
            user_data = requests.get(profile_url, headers=HEADERS).json()

            name = user_data.get("name") or username
            email = user_data.get("email") or ""

            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"     {index}/50 at {current_time} {profile_url}                   ", end="\r", flush=True)

            if is_personal_email(email) and is_personal_username(name) and not email_exists(email):
                logging.info(f"{name}\t{email}")
                with open("scan_email_list.log", "a", encoding="utf-8") as f:
                    f.write(email + "\n")
                EMAIL_SET.add(email.strip().lower())
                detectcnt += 1

            cnt += 1
            if cnt >= totalcnt:
                break

        print(f"\n---- Page {page}: {detectcnt} / 50 detected ----")
        alldetectcnt += detectcnt

        if (page - start_page + 1) * 50 >= totalcnt or cnt >= totalcnt:
            break

        time.sleep(1)  # Respect GitHub API rate limit

    print(f"\n---- Finished scanning {cnt}/{totalcnt} users. Total detected: {alldetectcnt} ----")
    print(result)

# ---------------- ENTRY ------------------
if __name__ == "__main__":
    args = parse_args()
    scan_users(*args)
