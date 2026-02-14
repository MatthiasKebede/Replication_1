"""
Data Collection Script (Part 2)
"""

import os
import sys
import re
import csv
from git import Repo


def check_user_intended(tag_name):
    """Look for pre/beta/alpha/rc releases"""
    if any(word in tag_name.lower() for word in ['alpha', 'beta', 'rc', 'pre']):
        print(f"Unintended: {tag_name}")
        return False
    return True


def collect_release_info(repo_name):
    # File handling
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'{repo_name}_releases_raw.csv')
    linked_file = os.path.join(output_dir, f'{repo_name}_releases_linked.csv')
    
    local_repo_path = os.path.join(script_dir, '..', '..', 'temp_repos', repo_name)
    if not os.path.isdir(local_repo_path):
        print("Repo path not found")
        sys.exit(1)



    # Collect info w/ GitPython
    repo = Repo(local_repo_path)
    all_tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime) # consider sorting backwards to match other data
    real_tags = [tag for tag in all_tags if check_user_intended(tag.name)]
    merge_pattern = re.compile(r"Merge pull request #(\d+)")
    releases_data = []
    releases_map = {}

    for i in range(len(real_tags) - 1):
        start_tag = real_tags[i]
        end_tag = real_tags[i+1]
        release_info = {'title': end_tag.name, # temp
            "publish_date": end_tag.commit.committed_datetime.isoformat(),
            "start_date": start_tag.commit.committed_datetime.isoformat(),
            "number_of_commits": 0, "number_of_prs": 0
        }

        # Get commits from between the tags
        commit_range = f'{start_tag.name}..{end_tag.name}' # commits reachable from end_tag but not from start_tag
        pr_numbers = set() # only count PRs once
        for commit in repo.iter_commits(commit_range):
            release_info["number_of_commits"] += 1
            match = merge_pattern.search(commit.message) # check if commit message has merge format
            if match:
                pr_number = int(match.group(1))
                pr_numbers.add(pr_number) # add PR number to set
                releases_map[pr_number] = end_tag.name # map PR to release name
        
        release_info["number_of_prs"] = len(pr_numbers)
        releases_data.append(release_info)

    if not releases_data or not releases_map:
        print("No release data and/or PR mapping, double-check repo and code")
        return



    # Save release information to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        fields = ['title', 'publish_date', 'start_date', 'number_of_commits', 'number_of_prs']
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(releases_data)

    # Save PR-to-release mapping to separate CSV
    with open(linked_file, 'w', newline='', encoding='utf-8') as file:
        fields = ['pull_number', 'release_tag']
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for pr_num, release_tag in releases_map.items():
            writer.writerow({'pull_number': pr_num, 'release_tag': release_tag})

    print(f"Saved release info for repo '{repo_name}'")


def main():
    if len(sys.argv) != 2:
        print("Usage: python collect_releases.py <repo_name>")
        sys.exit(1)
    
    repo = sys.argv[1]
    collect_release_info(repo)


if __name__ == '__main__':
    main()
