
import github
import pandas as pd
from datetime import datetime

# Get the repositories
g = github.Github("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")
repo_list = [g.get_repo("project-chip/connectedhomeip"), g.get_repo("CHIP-Specifications/chip-test-plans"), g.get_repo("CHIP-Specifications/chip-test-scripts")]

# Get all issues
data = pd.DataFrame()
for repo in repo_list:
    repo_name = repo.name
    issues = repo.get_issues(state="all")
    df = pd.DataFrame([[repo_name, issue.number, issue.created_at, issue.state, issue.title, issue.closed_at, issue.html_url] for issue in issues], columns=["Repo Name", "Issue ID", "Created Date", "State", "Title", "Closed Date", "URL"])
    data = pd.concat([data, df], ignore_index=True, sort=False)

# Export all issues
filename = "matter_issue_" + datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + ".xlsx"
data.to_excel(filename, index=False)
