import os
import time
import requests
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import json
import yaml

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def fetch_issues_from_repo(repo_name, github_token):
    api_url = f"https://api.github.com/repos/{repo_name}/issues"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching issues from {repo_name}. Status code: {response.status_code}")
        return []

# Update Google Sheets with fetched issues data
def update_google_sheets(issues_data, service_account_json):
    service_account_json_dict = json.loads(service_account_json)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_json_dict, scope)
    gc = gspread.authorize(credentials)
    
    sh = gc.open("Matterissues")
    for repo_name, issues in issues_data.items():
        worksheet_name = f"{repo_name}_issues"
        try:
            worksheet = sh.worksheet(worksheet_name)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=worksheet_name, rows=str(len(issues) + 1), cols=9)
            print(f"Created a worksheet named {worksheet_name} for the repo name {repo_name}")
        headers = ["Repo Name", "Issue ID", "State", "Title", "Author", "Label", "Created Date", "Closed Date", "URL"]
        worksheet.update([headers] + issues)
        print(f"Updated the sheet {worksheet_name} with {repo_name} repo issues")

if __name__ == "__main__":
    with open("src/repos.yml", "r") as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    repo_names = yaml_data["repos"]

    github_token = os.environ.get("MY_GITHUB_TOKEN")

    issues_data = {}
    for repo_name in repo_names:
        issues = fetch_issues_from_repo(repo_name, github_token)
        issues_data[repo_name] = issues

    service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")
    update_google_sheets(issues_data, service_account_json)

    print("Sheet is updated")
