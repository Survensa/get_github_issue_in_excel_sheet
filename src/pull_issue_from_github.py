import os
import time
import github
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import json
import yaml

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

# Fetch GitHub issues for each repository
def fetch_github_issues(github_token, repo_names):
    g = github.Github(github_token)
    repo_list = [g.get_repo(repo_name) for repo_name in repo_names]
    issues_data = []
    for repo in repo_list:
        repo_name = repo.name
        print("Fetching issues for repo:", repo_name)
        issues = repo.get_issues(state="all")
        issues_data.extend([[repo_name, issue.number, issue.state, issue.title, issue.user.login, issue.labels,
                             issue.created_at, issue.closed_at, issue.html_url] for issue in issues])
    return issues_data

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
    issues_data = fetch_github_issues(github_token, repo_names)

    service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")
    update_google_sheets(issues_data, service_account_json)

    print("Sheet is updated")
