#!/usr/bin/env python3
# Work with Python 3

import json
import shutil

from git import Repo

PROJECT_PATH = "/home/ciripel/Programe/SnowgemDevelopmentProgress"


file = open("dev-diary.json", "r")
thelist = file.read()
file.close()
listed = json.loads(thelist)
total_commits = len(listed)


def description(index):
    if listed[index]["author"] == "shmocs":
        return listed[index]["content"]
    else:
        return "[" + listed[index]["embed_0"]["title"] + "](" + listed[index]["embed_0"]["url"] + ")"


def commit(index):
    if listed[index]["author"] == "shmocs":
        raw_commits = listed[index]["embed_0"]["description"]
        raw_commits = raw_commits.replace("\n\n", "<br>")
        raw_commits = raw_commits.replace("\n", "")
        return raw_commits
    elif listed[index]["author"] == "GitHub":
        raw_commits = listed[index]["embed_0"]["description"]
        raw_commits = raw_commits.replace("\n", "<br>")
        raw_commits = raw_commits.replace("`", "")
        return raw_commits
    else:
        raw_commits = ""
        for i in range(len(listed[index]["embed_0"]["fields"])):
            raw_commits = raw_commits + "<br>" + listed[index]["embed_0"]["fields"][i]["value"]
        raw_commits = raw_commits[4:]
        raw_commits = raw_commits.replace("`", "")
        return raw_commits


shutil.copy("dev-diary.json", PROJECT_PATH)

file = open(PROJECT_PATH + "/Complete_list.md", "w")
message = """
### Snowgem Development Progress - Complete history

Here is the complete list of all the commits to the projects we are currently working since 20/01/2020.

| Push Time | Description | Commits |
| --- | --- | --- |
{table}

_You can see more details and commits in our [Discord](https://discord.gg/zumGnbg) in **#dev-diary** channel._
""".format(
    table="\n".join(
        "| <sub>{}</sub> | <sub>{}</sub> | <sub>{}</sub> |".format(
            listed[total_commits - i - 1]["created_at"][:-7],
            description(total_commits - i - 1),
            commit(total_commits - i - 1),
        )
        for i in range(total_commits)
    )
)
file.write(message)
file.close()
complete_listed = listed

listed = listed[-10:]
total_commits = len(listed)
file = open(PROJECT_PATH + "/README.md", "w")
message = """
### Snowgem Development Progress

Here are the last 10 pushes to the projects we are currently working.

There is a total of {total_commits} commits since 20/01/2020. You can see the complete history in
 [Complete_list.md](Complete_list.md) file.

| Push Time | Description | Commits |
| --- | --- | --- |
{table}

_You can see more details and commits in our [Discord](https://discord.gg/zumGnbg) in **#dev-diary** channel._
""".format(
    total_commits=total_commits,
    table="\n".join(
        "| <sub>{}</sub> | <sub>{}</sub> | <sub>{}</sub> |".format(
            listed[total_commits - i - 1]["created_at"][:-7],
            description(total_commits - i - 1),
            commit(total_commits - i - 1),
        )
        for i in range(total_commits)
    ),
)
file.write(message)
file.close()


PATH_OF_GIT_REPO = PROJECT_PATH + "/.git"  # make sure .git folder is properly configured
COMMIT_MESSAGE = "Last work at " + complete_listed[-1]["created_at"][:-7]


def git_push():
    try:
        repo = Repo(PATH_OF_GIT_REPO)
        repo.git.add(update=True)
        repo.git.commit(m=COMMIT_MESSAGE)
        origin = repo.remote(name="origin")
        origin.push()
        sha = repo.head.object.hexsha
        print(f"On branch master.\nPushed commit {sha}")
    except Exception:
        print(
            "On branch master.\nYour branch is up to date with 'origin/master'.\nNothing to commit, working tree clean."
        )


git_push()
