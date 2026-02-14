"""
Data Collection Script (Part 2)
"""

import os
import sys
import re
import csv
from pydriller import Repository, Git


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



    # Collect info w/ pydriller
    repo = Repository(local_repo_path)
    releases_data = []
    

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
