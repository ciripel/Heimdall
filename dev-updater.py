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

created_at_1 = listed[-1]["created_at"][:-7]
created_at_2 = listed[-2]["created_at"][:-7]
created_at_3 = listed[-3]["created_at"][:-7]
created_at_4 = listed[-3]["created_at"][:-7]
created_at_5 = listed[-3]["created_at"][:-7]

shutil.copy('dev-diary.json', PROJECT_PATH)
file = open(PROJECT_PATH + "/README.md", "w")
message = f"""
### Snowgem Development Progress

Here are the last 5 pushes to the projects we are currently working.

There is a total of {total_commits} commits since 20/01/2020. You can see the complete history in **dev-diary.json** file.

| Push Time | Description | Commits |
| --- | --- | --- |
| {created_at_1} |  |  |
| {created_at_2} |  |  |
| {created_at_3} |  |  |
| {created_at_4} |  |  |
| {created_at_5} |  |  |

_You can see more details and commits in our [Discord](https://discord.gg/zumGnbg) in **#dev-diary** channel._
"""
file.write(message)
file.close()

PATH_OF_GIT_REPO = PROJECT_PATH + "/.git"  # make sure .git folder is properly configured
COMMIT_MESSAGE = 'comment from python script'


def git_push():
    try:
        repo = Repo(PATH_OF_GIT_REPO)
        repo.git.add(update=True)
        repo.git.commit(m=COMMIT_MESSAGE)
        origin = repo.remote(name='origin')
        origin.push()
        sha = repo.head.object.hexsha
        print(f"On branch master.\nPushed commit {sha}")
    except Exception:
        print("On branch master.\nYour branch is up to date with 'origin/master'.\nNothing to commit, working tree clean.")


git_push()
