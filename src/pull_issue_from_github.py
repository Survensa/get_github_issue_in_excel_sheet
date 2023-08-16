import time
import os
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import json
import requests
import yaml

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

with open("src/repos.yml", "r") as yaml_file:
    yaml_data = yaml.safe_load(yaml_file)
repo_names = yaml_data["repos"]

github_token = os.environ.get("MY_GITHUB_TOKEN")
service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")

api_base_url = "https://api.github.com"
headers = {
    "Authorization": f"Bearer {github_token}",
    "Accept": "application/vnd.github.v3+json"
}

credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(service_account_json), [
    'https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
gc = gspread.authorize(credentials)

api_request_delay = 60  # Adjust as needed, in seconds

for repo_name in repo_names:
    start_time = time.time()
    print("Fetching issues for repo:", repo_name)
    issues_url = f"{api_base_url}/repos/{repo_name}/issues"
    issues_response = requests.get(issues_url, headers=headers)
    if issues_response.status_code == 200:
        issues_data = issues_response.json()
        print("Fetched issues data:", issues_data)  # Add this line to print the issues data
        
        df = pd.DataFrame([
            [repo_name, issue['number'], issue['state'], issue['title'], issue['user']['login'],
             ", ".join([label['name'] for label in issue['labels']]),
             issue['created_at'], issue.get('closed_at', None), issue['html_url']] for issue in issues_data],
            columns=["Repo Name", "Issue ID", "State", "Title", "Author", "Label", "Created Date", "Closed Date", "URL"])
    
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
        worksheet_name = f"{repo_name}_issues"
        try:
            worksheet = sh.worksheet(worksheet_name)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=worksheet_name, rows=str(len(df) + 1), cols=9)
            print(f"Created a worksheet named {worksheet_name} for the repo {repo_name}")
    
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
