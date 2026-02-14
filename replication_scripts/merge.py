"""
Data Collection Script (Step 3)

Reads from generated CSVs in Step 1 & 2, calculates metrics and produces final CSV output.
"""

import os
import sys
import csv


def consolidate_data(owner, repo_name):
    # File handling
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, '..', 'outputs')
    pulls_file = os.path.join(output_dir, f'{owner}_{repo_name}_pulls_raw.csv')
    linking_file = os.path.join(output_dir, f'{repo_name}_releases_linked.csv')
    merged_file = os.path.join(output_dir, f'{repo_name}_data_merged.csv')

    if not os.path.exists(pulls_file) or not os.path.exists(linking_file):
        print("Couldn't find CSV input files, check args or try running data collection scripts")
        sys.exit(1)

    # Read from 'linking' file
    releases_map = {}
    with open(linking_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            releases_map[row['pull_number']] = row['release_tag']
    
    # Read from raw PR file
    with open(pulls_file,'r',encoding='utf-8') as pr,open(merged_file,'w',newline='',encoding='utf-8') as out:
        reader = csv.DictReader(pr)
        fields = reader.fieldnames + ['release_tag']
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()

        for row in reader:
            pr_number = row['pull_number']
            release_tag = releases_map.get(pr_number)
            row['release_tag'] = release_tag
            writer.writerow(row)


def main():
    if len(sys.argv) != 3:
        print("Usage: python merge.py <owner> <repo_name>")
        sys.exit(1)
    
    owner = sys.argv[1]
    repo_name = sys.argv[2]
    consolidate_data(owner, repo_name)


if __name__ == '__main__':
    main()
