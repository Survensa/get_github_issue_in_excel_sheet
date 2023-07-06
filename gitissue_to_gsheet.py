import github
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

g = github.Github("<TOKEN>")
repo_list = [g.get_repo("project-chip/connectedhomeip"), g.get_repo("CHIP-Specifications/chip-test-plans"), g.get_repo("CHIP-Specifications/chip-test-scripts"), g.get_repo("CHIP-Specifications/chip-certification-tool")]

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('C:/Users/suraj/Suraj_Personal/Auto/Gsheetissue/Matterissue.json',scope)
gc = gspread.authorize(credentials)

for repo in repo_list:
    repo_name = repo.name
    issues = repo.get_issues(state="all")
    df = pd.DataFrame([[repo_name, issue.number, issue.state, issue.title, issue.user.login, issue.labels, issue.created_at,
                        issue.closed_at, issue.html_url] for issue in issues],
                      columns=["Repo Name", "Issue ID", "State", "Title", "Author", "Label", "Created Date",  "Closed Date",
                               "URL"])
    df["Label"] = df["Label"].apply(lambda x: '"{0}"'.format(", ".join([label.name for label in x])) if x else None)
    df["Created Date"] = df["Created Date"].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    df["Closed Date"] = df["Closed Date"].apply(
        lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x and not pd.isnull(x) else None)

    print("Processing repo {}".format(repo_name))
    sh = gc.open("Matterissues")
    worksheet_name = "{}_issues".format(repo_name)
    try:
        worksheet = sh.worksheet(worksheet_name)
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=worksheet_name, rows=str(len(df) + 1), cols=9)
    cell_list = worksheet.range(1, 1, 1, 9)
    worksheet.format('A1:I1', {'textFormat': {'bold': True, 'fontFamily': 'Times New Roman'},
                               'horizontalAlignment': 'CENTER'})
    worksheet.format('A2:I', {'textFormat': {'fontFamily': 'Times New Roman'}, 'wrapStrategy': 'WRAP',
                              'verticalAlignment': 'MIDDLE'})
    worksheet.format('A2:C', {'horizontalAlignment': 'CENTER'})
    worksheet.format('G2:H', {'horizontalAlignment': 'CENTER'})
    for t, cell in zip(df.columns, cell_list):
        cell.value = t
    worksheet.update_cells(cell_list)
    cell_list = worksheet.range(2, 1, len(df) + 1, 9)
    for t, cell in zip(df.values.flatten(), cell_list):
        cell.value = t
    worksheet.update_cells(cell_list)
print("Sheet is updated")
