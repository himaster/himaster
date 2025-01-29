import os
import sys
import shutil
import random
import subprocess
import math
from datetime import datetime, timedelta
from collections import defaultdict

def ask(prompt):
    return input(prompt)

def perform_clone(repository, repo_path, repo_url):
    if os.path.exists(repo_path):
        answer = os.getenv("FORCE_REMOVE") or ask(
            f"The directory '{repository}' already exists. Would you like to remove it and continue? [y/N]: "
        )

        if answer.lower() == "y":
            try:
                shutil.rmtree(repo_path)
                print(f"The directory '{repository}' has been removed.")
            except Exception as err:
                print(f"Error while removing the directory: {err}")
                sys.exit(1)
        else:
            print("Operation cancelled by the user.")
            sys.exit(0)

    print(f"git clone {repo_url} {repo_path}")
    subprocess.run(["git", "clone", repo_url, repo_path], check=True)

def perform_commit(username, repository, repo_path, day):
    formatted_date = f"{day.strftime('%Y-%m-%d')}T12:{random_number_0_to_59()}:{random_number_0_to_59()}"
    commit_message = f"Committed on {formatted_date}"
    readme_content = f"{commit_message} \nCommitter - https://github.com/{username}/{repository}"
    
    with open(f"{repo_path}/README.md", "w") as file:
        file.write(readme_content)

    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_DATE": formatted_date,
        "GIT_COMMITTER_DATE": formatted_date,
    })

    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_path, env=env, check=True)

def perform_git_operations_stochastic(username, access_token, repository, start_date, end_date, ratios, appear_probabilities, max_commits):
    repo_path = os.path.join(os.getcwd(), "repos", repository)
    repo_url = f"https://{access_token}@github.com/{username}/{repository}.git"
    perform_clone(repository, repo_path, repo_url)

    week_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day = start_date

    while day <= end_date:
        day_week = week_days[day.weekday()]
        random_num = random.random()
        ratio = ratios[day_week]
        appear_probability = appear_probabilities[day_week]
        
        if appear_probability > random_num:
            ratio_random = get_random_normal_distribution(ratio, 0.3)
            num_commits = max(0, int(ratio_random * max_commits))

            for _ in range(num_commits):
                perform_commit(username, repository, repo_path, day)

            subprocess.run(["git", "push"], cwd=repo_path, env={"GITHUB_TOKEN": access_token}, check=True)

        day += timedelta(days=1)

    print(f"Committed from {start_date} to {end_date}. Check out your profile: https://github.com/{username}")
    sys.exit(0)

def perform_git_operations_constant(username, access_token, repository, start_date, end_date):
    repo_path = os.path.join(os.getcwd(), repository)
    repo_url = f"https://{access_token}@github.com/{username}/{repository}.git"
    perform_clone(repository, repo_path, repo_url)

    day = start_date
    while day <= end_date:
        perform_commit(username, repository, repo_path, day)
        day += timedelta(days=1)

    subprocess.run(["git", "push"], cwd=repo_path, env={"GITHUB_TOKEN": access_token}, check=True)
    print(f"Committed from {start_date} to {end_date}. Check out your profile: https://github.com/{username}")
    sys.exit(0)

def random_number_0_to_59():
    return str(random.randint(0, 59)).zfill(2)

def get_random_normal_distribution(mean, standard_deviation):
    u, v = random.random(), random.random()
    z = (-2 * math.log(u)) ** 0.5 * math.cos(2 * math.pi * v)
    return z * standard_deviation + mean

def main():
    mode = os.getenv("COMMIT_MODE") or ask("Enter the commit mode (random, fix): ")
    username = os.getenv("GITHUB_USERNAME") or ask("Enter your GitHub username: ")
    access_token = os.getenv("GITHUB_TOKEN") or ask("Enter your GitHub access token: ")
    repository = os.getenv("GITHUB_REPO") or ask("Enter your GitHub repository name: ")
    
    start_date = datetime.today() if os.getenv("START_DATE") else datetime.strptime(ask("Enter start date (YYYY-MM-DD): "), "%Y-%m-%d")
    end_date = datetime.today() if os.getenv("END_DATE") else datetime.strptime(ask("Enter end date (YYYY-MM-DD): "), "%Y-%m-%d")

    if mode == "fix":
        perform_git_operations_constant(username, access_token, repository, start_date, end_date)
    else:
        week_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        ratios = {}
        appear_probabilities = {}
        max_commits = int(os.getenv("MAX_COMMIT_NUMBER") or ask("Enter the maximum number of commits: "))

        for day in week_days:
            ratios[day] = float(os.getenv(f"RATIO_{day}", None) or ask(f"Enter the {day} ratio to max commits (0 to 1): "))
            appear_probabilities[day] = float(os.getenv(f"PROBABILITY_{day}", None) or ask(f"Enter the {day} appear probability (0 to 1): "))

        perform_git_operations_stochastic(username, access_token, repository, start_date, end_date, ratios, appear_probabilities, max_commits)

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("An error occurred:", error)
        sys.exit(1)
