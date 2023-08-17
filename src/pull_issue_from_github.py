import os
import time
import requests
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import json
import yaml
import logging
import http.client as http_client

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def fetch_issues_from_repo(owner, repo, github_token):
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(api_url, headers=headers)
    print(f"API request response status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    
    github_request_id = response.headers.get("X-GitHub-Request-Id")
    print(f"GitHub Request ID: {github_request_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching issues from {owner}/{repo}. Status code: {response.status_code}")
        return []

# Enable verbose logging for requests
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

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
        data_rows = []
        for issue in issues:
            data_rows.append([repo_name, issue.get("number"), issue.get("state"), issue.get("title"),
                              issue.get("user", {}).get("login"), ", ".join(label.get("name") for label in issue.get("labels", [])),
                              issue.get("created_at"), issue.get("closed_at"), issue.get("html_url")])
        
        worksheet.append_row(headers)
        for row in data_rows:
            worksheet.append_row(row)
        
        print(f"Updated the sheet {worksheet_name} with {repo_name} repo issues")

if __name__ == "__main__":
    with open("repos.yml", "r") as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    repo_configs = yaml_data["repos"]

    github_token = os.environ.get("MY_GITHUB_TOKEN")

    issues_data = {}
    for repo_config in repo_configs:
        owner = repo_config["owner"]
        repo = repo_config["repo"]
        issues = fetch_issues_from_repo(owner, repo, github_token)
        issues_data[f"{owner}/{repo}"] = issues

    service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")
    update_google_sheets(issues_data, service_account_json)

    print("Sheet is updated")
