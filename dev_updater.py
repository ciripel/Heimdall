#!/usr/bin/env python3
# Work with Python 3

import json
import shutil

from git import Repo

PROJECT_PATH = "../SnowgemDevelopmentProgress"


with open("dev-diary.json") as data_file:
    complete_list = json.load(data_file)
    truncated_list = complete_list[-10:]

PATH_OF_GIT_REPO = PROJECT_PATH + "/.git"  # make sure .git folder is properly configured
COMMIT_MESSAGE = "Last work at " + complete_list[-1]["created_at"][:-7]


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


def description(the_list, index):
    if the_list[index]["author"] == "shmocs":
        return the_list[index]["content"]
    else:
        return "[" + the_list[index]["embed_0"]["title"] + "](" + the_list[index]["embed_0"]["url"] + ")"


def commit(the_list, index):
    if the_list[index]["author"] == "shmocs":
        raw_commits = the_list[index]["embed_0"]["description"]
        raw_commits = raw_commits.replace("\n\n", "<br>")
        raw_commits = raw_commits.replace("\n", "")
        return raw_commits
    elif the_list[index]["author"] == "GitHub":
        raw_commits = the_list[index]["embed_0"]["description"]
        raw_commits = raw_commits.replace("\n", "<br>")
        raw_commits = raw_commits.replace("`", "")
        return raw_commits
    else:
        raw_commits = ""
        for i in range(len(the_list[index]["embed_0"]["fields"])):
            raw_commits = raw_commits + "<br>" + the_list[index]["embed_0"]["fields"][i]["value"]
        raw_commits = raw_commits[4:]
        raw_commits = raw_commits.replace("`", "")
        return raw_commits


def dev_update():
    shutil.copy("dev-diary.json", PROJECT_PATH)
    file = open(PROJECT_PATH + "/Complete_list.md", "w")
    total_commits = len(complete_list)
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
                complete_list[total_commits - i - 1]["created_at"][:-7],
                description(complete_list, total_commits - i - 1),
                commit(complete_list, total_commits - i - 1),
            )
            for i in range(total_commits)
        )
    )
    file.write(message)
    file.close()

    total_commits = len(truncated_list)
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
        total_commits=len(complete_list),
        table="\n".join(
            "| <sub>{}</sub> | <sub>{}</sub> | <sub>{}</sub> |".format(
                truncated_list[total_commits - i - 1]["created_at"][:-7],
                description(truncated_list, total_commits - i - 1),
                commit(truncated_list, total_commits - i - 1),
            )
            for i in range(total_commits)
        ),
    )
    file.write(message)
    file.close()
    git_push()


dev_update()
