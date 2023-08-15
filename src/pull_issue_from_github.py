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

# Load repository names from YAML file
with open("src/repos.yml", "r") as yaml_file:
    yaml_data = yaml.safe_load(yaml_file)
repo_names = yaml_data["repos"]

# Access GitHub token and Service Account JSON from environment variables
github_token = os.environ.get("GITHUB_TOKEN")
service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")

# Use github_token in your GitHub API authentication
g = github.Github(github_token)

# Load Service Account JSON from environment variable
service_account_json_dict = json.loads(service_account_json)

# Authenticate with Service Account JSON
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_json_dict, scope)
gc = gspread.authorize(credentials)

# Initialize a delay to avoid hitting the rate limit
api_request_delay = 60  # Adjust as needed, in seconds

for repo_name in repo_names:
    try:
        repo = g.get_repo(repo_name)
        repo_name = repo.name
        start_time = time.time()
        print("Fetching issues for repo:", repo_name)
        issues = repo.get_issues(state="all")
        
        # Process issues and update the worksheet
        df = pd.DataFrame([[repo_name, issue.number, issue.state, issue.title, issue.user.login, issue.labels, issue.created_at,
                            issue.closed_at, issue.html_url] for issue in issues],
                          columns=["Repo Name", "Issue ID", "State", "Title", "Author", "Label", "Created Date",  "Closed Date",
                                   "URL"])
        df["Label"] = df["Label"].apply(lambda x: '"{0}"'.format(", ".join([label.name for label in x])) if x else None)
        df["Created Date"] = df["Created Date"].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
        df["Closed Date"] = df["Closed Date"].apply(
            lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x and not pd.isnull(x) else None)
        end_time = time.time()
        duration_seconds = end_time - start_time
        duration = format_duration(duration_seconds)
        print(f"Fetch Completed for repo {repo_name}: {duration}")
        print("Processing issues for repo:", repo_name)
        
        # Introduce a delay to avoid exceeding the GitHub API rate limit
        time.sleep(api_request_delay)
        
        # Update the Google Sheet
        sh = gc.open("Matterissues")
        worksheet_name = "{}_issues".format(repo_name)
        try:
            worksheet = sh.worksheet(worksheet_name)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=worksheet_name, rows=str(len(df) + 1), cols=9)
            print(f"Created a worksheet named {worksheet} for the repo name {repo_name}")
        cell_list = worksheet.range(1, 1, 1, 9)
        for t, cell in zip(df.columns, cell_list):
            cell.value = t
        worksheet.update_cells(cell_list)
        cell_list = worksheet.range(2, 1, len(df) + 1, 9)
        for t, cell in zip(df.values.flatten(), cell_list):
            cell.value = t
        worksheet.update_cells(cell_list)
        print(f"Updated the sheet {worksheet} with {repo_name} repo issues")
        
    except github.GithubException as e:
        print(f"Error fetching issues for repo {repo_name}: {e}")
    except Exception as e:
        print(f"An error occurred for repo {repo_name}: {e}")

print("All repos processed")
