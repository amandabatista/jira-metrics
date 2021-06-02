# This is a sample Python script.
from atlassian import Jira
import pandas as pd
import workdays

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def search_jira(name):
    jira_instance = Jira(
        url="",
        username="",
        password="",
    )

    issue_query_str = ("project = PP AND status in (\"DONE this week\", Done) AND "
                       "resolved >= 2021-04-22 AND resolved <= 2021-05-21 "
                       "AND issuetype in (Bug, Story, Task) "
                       "AND (fixVersion = \"Delivery Infra Release 12\" OR "
                       "fixVersion = \"Delivery Infra Release 11\" OR "
                       "fixVersion = \"Delivery Infra Release 10\")")

    response = jira_instance.jql(jql=issue_query_str,
                                 limit=200,
                                 fields=["issuetype", "status", "summary", "resolutiondate", "labels"])
    df = pd.json_normalize(response["issues"])

    FIELDS_OF_INTEREST = ["key", "fields.summary", "fields.issuetype.name", "fields.status.name", "fields.resolutiondate", "fields.labels"]

    df = df[FIELDS_OF_INTEREST]

    df = df.rename(columns={"fields.summary": "Summary",
                            "fields.issuetype.name": "Issue_Type",
                            "fields.status.name": "Status",
                            "fields.resolutiondate": "Resolution_Date_Str",
                            "fields.labels": "Labels"})

    df['Resolution_Date_Str'] = df['Resolution_Date_Str'].str.slice(0, 10)
    df['Resolution_Date'] = pd.to_datetime(df['Resolution_Date_Str'], format='%Y-%m-%d')
    del df['Resolution_Date_Str']
    df["start_at"] = ""
    df["duration"] = ""

    for i in df.index:
        transition_resp = jira_instance.get_issue_changelog(df['key'][i])
        df_histories = pd.json_normalize(transition_resp["histories"])
        df_histories['created_str'] = df_histories['created'].str.slice(0, 10)
        df_histories['created_at'] = pd.to_datetime(df_histories['created_str'], format='%Y-%m-%d')
        df_histories.sort_values('created_at')
        for h in df_histories.index:
            df_items = pd.json_normalize(df_histories['items'][h])
            for j in df_items.index:
                if (df_items["toString"][j] == "Done") and ((df_items["fromString"][j] == "Pipeline") or\
                                                            (df_items["fromString"][j] == "To Do")):
                    df["start_at"][i] = df_histories['created_at'][h]
                    df["duration"][i] = workdays.networkdays(df_histories['created_at'][h], df['Resolution_Date'][i])
                    # df["duration"][i] = (df['Resolution_Date'][i] - df_histories['created_at'][h]).days #workdays
                    break

                if (df_items["toString"][j] == "Doing") or (df_items["toString"][j] == "Working") or\
                        (df_items["toString"][j] == "In Progress") or (df_items["toString"][j] == "Development"):
                    df["start_at"][i] = df_histories['created_at'][h]
                    df["duration"][i] = workdays.networkdays(df_histories['created_at'][h], df['Resolution_Date'][i])
                    # df["duration"][i] = (df['Resolution_Date'][i] - df_histories['created_at'][h]).days #workdays
                    break

    df.to_excel("output.xlsx")

    # Use a breakpoint in the code line below to debug your script.
    # print(f'Hi, {df}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    search_jira('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
