from github import Github
import pandas as pd

# Get the repository
g = Github("<GIT_ACCESS_TOKEN")

repo = g.get_repo("project-chip/connectedhomeip")

# store the data in the list
data = []

for issue in repo.get_issues(state="all"):
    data.append([repo_name, issue.number, issue.labels, issue.created_at, issue.state, issue.title, issue.closed_at, issue.html_url])

df = pd.DataFrame(data, columns=["Repo Name", "Issue ID", "Label", "Created Date", "State", "Title", "Closed Date", "URL"])
df["Label"] = df["Label"].apply(lambda x: [label.name for label in x])
df["Label"] = df["Label"].apply(lambda x: '"{0}"'.format(", ".join(x)))
df.to_excel("gitissues.xlsx", index=False)
