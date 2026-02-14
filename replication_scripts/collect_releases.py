"""
Data Collection Script (Part 2)
"""

import os
import sys
import re
import csv
from git import Repo


def collect_release_info(repo_name):
    # File handling
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'{repo_name}_releases_raw.csv')
    
    local_repo_path = os.path.join(script_dir, '..', '..', 'temp_repos', repo_name)
    if not os.path.isdir(local_repo_path):
        print("Repo path not found")
        sys.exit(1)



    # Collect info w/ GitPython
    repo = Repo(local_repo_path)
    tags = repo.tags
    releases_data = []
    merge_pattern = re.compile(r"Merge pull request #(\d+)")

    for i in range(len(tags) - 1):
        start_tag = tags[i]
        end_tag = tags[i+1]
        release_info = {
            "publish_date": end_tag.commit.committed_datetime.isoformat(),
            "start_date": start_tag.commit.committed_datetime.isoformat(),
            "number_of_commits": 0, "number_of_prs": 0
        }

        # Get commits from between the tags
        commit_range = f'{start_tag.name}..{end_tag.name}'
        pr_numbers = set() # only count PRs once
        for commit in repo.iter_commits(commit_range):
            release_info["number_of_commits"] += 1
            match = merge_pattern.search(commit.message) # check if commit message has merge format
            if match:
                pr_numbers.add(int(match.group(1))) # add PR number to the set
        
        release_info["number_of_prs"] = len(pr_numbers)
        releases_data.append(release_info)

    if not releases_data:
        print("No release data, double-check repo and code")
        return



    # Save to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        fields = ['publish_date', 'start_date', 'number_of_commits', 'number_of_prs']
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(releases_data)


def main():
    if len(sys.argv) != 2:
        print("Usage: python collect_releases.py <repo_name>")
        sys.exit(1)
    
    repo = sys.argv[1]
    collect_release_info(repo)


if __name__ == '__main__':
    main()
