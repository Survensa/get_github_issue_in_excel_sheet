import time
import os
import github
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import yaml
import json

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

with open("src/repos.yml", "r") as yaml_file:
    yaml_data = yaml.safe_load(yaml_file)
repo_names = yaml_data["repos"]

github_token = os.environ.get("MY_GITHUB_TOKEN")
service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")

g = github.Github(github_token)
service_account_json_dict = json.loads(service_account_json)
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_json_dict, scope)
gc = gspread.authorize(credentials)

api_request_delay = 60  # Adjust as needed, in seconds

for repo_name in repo_names:
    repo = g.get_repo(repo_name)
    repo_name = repo.name
    start_time = time.time()
    print("Fetching issues for repo:", repo_name)
    
    issue_list = []  # Create an empty list to store issue dictionaries
    
    for issue in repo.get_issues(state="all"):
        issue_dict = {
            "repo_name": repo_name,
            "issue_id": issue.number,
            "state": issue.state,
            "title": issue.title,
            "author": issue.user.login,
            "labels": [label.name for label in issue.labels],
            "created_date": issue.created_at,
            "closed_date": issue.closed_at,
            "url": issue.html_url
        }
        issue_list.append(issue_dict)

    df = pd.DataFrame(issue_list, columns=["Repo Name", "Issue ID", "State", "Title", "Author", "Label", "Created Date", "Closed Date", "URL"])
    df["Label"] = df["Label"].apply(lambda x: '"{0}"'.format(", ".join([label.name for label in x])) if x else None)
    df["Created Date"] = df["Created Date"].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    df["Closed Date"] = df["Closed Date"].apply(
        lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x and not pd.isnull(x) else None)
    end_time = time.time()
    duration_seconds = end_time - start_time
    duration = format_duration(duration_seconds)
    print(f"Fetch Completed for repo {repo_name}: {duration}")
    print("Processing issues for repo:", repo_name)

    time.sleep(api_request_delay)

    sh = gc.open("Matterissues")
    worksheet_name = "{}_issues".format(repo_name)
    try:
        worksheet = sh.worksheet(worksheet_name)
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=worksheet_name, rows=str(len(df) + 1), cols=9)
        print(f"Created a worksheet named {worksheet_name} for the repo name {repo_name}")
    cell_list = worksheet.range(1, 1, 1, 9)
    for t, cell in zip(df.columns, cell_list):
        cell.value = t
    worksheet.update_cells(cell_list)
    cell_list = worksheet.range(2, 1, len(df) + 1, 9)
    for t, cell in zip(df.values.flatten(), cell_list):
        cell.value = t
    worksheet.update_cells(cell_list)
    print(f"Updated the sheet {worksheet_name} with {repo_name} repo issues")
    
    time.sleep(api_request_delay)

print("All repos processed")
