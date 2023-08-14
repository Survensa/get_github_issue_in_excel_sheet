import github
import pandas as pd
from datetime import datetime
import yaml

# Get the repositories
with open("repos.yml", "r") as yaml_file:
    yaml_data = yaml.safe_load(yaml_file)
repo_names = yaml_data["repos"]

g = github.Github("<GIT_ACCESS_TOKEN")
repo_list = [g.get_repo(repo_name) for repo_name in repo_names]

filename = "Github_Issue_" + datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + ".xlsx"

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
    df = pd.DataFrame([[repo_name, issue.number, issue.labels, issue.created_at, issue.state, issue.title, issue.closed_at, issue.html_url] for issue in issues], columns=["Repo Name", "Issue ID", "Label", "Created Date", "State", "Title", "Closed Date", "URL"])
    df["Label"] = df["Label"].apply(lambda x: [label.name for label in x])
    df["Label"] = df["Label"].apply(lambda x: '"{0}"'.format(", ".join(x)))
    df.to_excel(writer, sheet_name=repo_name, index=False)
writer.close()
print("Issue is saved in :", filename)
