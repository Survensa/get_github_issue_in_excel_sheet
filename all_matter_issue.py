import github
import pandas as pd
from datetime import datetime

# Get the repositories
g = github.Github("<GIT_ACCESS_TOKEN>")
repo_list = [g.get_repo("project-chip/connectedhomeip"), g.get_repo("CHIP-Specifications/chip-test-plans"), g.get_repo("CHIP-Specifications/chip-test-scripts")]

filename = "matter_issue_" + datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + ".xlsx"

# Get all issues in single sheet
#data = pd.DataFrame()
#for repo in repo_list:
#    repo_name = repo.name
#    issues = repo.get_issues(state="all")
#    df = pd.DataFrame([[repo_name, issue.number, issue.created_at, issue.state, issue.title, issue.closed_at, issue.html_url] for issue in issues], columns=["Repo Name", "Issue ID", "Created Date", "State", "Title", "Closed Date", "URL"])
#    data = pd.concat([data, df], ignore_index=True, sort=False)
#data.to_excel(filename, index=False)

# Export all issues in seperate sheet
writer = pd.ExcelWriter(filename)
for repo in repo_list:
    repo_name = repo.name
    issues = repo.get_issues(state="all")
    df = pd.DataFrame([[repo_name, issue.number, issue.created_at, issue.state, issue.title, issue.closed_at, issue.html_url] for issue in issues], columns=["Repo Name", "Issue ID", "Created Date", "State", "Title", "Closed Date", "URL"])
    df.to_excel(writer, sheet_name=repo_name, index=False)
writer.close()
