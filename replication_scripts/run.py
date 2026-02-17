import argparse
import sys
import os

# Import your modules
from collect_pulls import collect_pull_requests
from collect_releases import collect_release_info
from merge import consolidate_data
from metrics import dataSetup, analysis


script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, '..', 'outputs')


def run_pipeline(owner: str, repo: str):
    """
    Runs the full replication pipeline for a single repository.
    """
    print(f"\n===== Running pipeline for {owner}/{repo} =====")

    try:
        print("Step 1: Collecting pull requests...")
        collect_pull_requests(owner, repo)

        print("Step 2: Collecting releases...")
        collect_release_info(owner, repo)

        print("Step 3: Merging data...")
        consolidate_data(owner, repo)

        print("Step 4: Computing metrics...")
        before_ci, after_ci =  dataSetup(repo, owner)

        analysis(before_ci, after_ci, repo,"../outputs/results_from_minned_data.csv",owner)


        print(f"===== Completed {owner}/{repo} =====\n")

    except Exception as e:
        print(f"Error while processing {owner}/{repo}: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) > 3:
        print("Usage: python run.py <repo> <owner>")
        print("Example: python run.py mrjob Yelp")
        print("If you don't give any repo, it will run for 5 repos we minned")
        sys.exit(1)
    elif len(sys.argv) == 3:
        repo = sys.argv[1]
        owner = sys.argv[2]
    
    # Case 1: Single repo via CLI
        run_pipeline(owner, repo)

    # Case 2: Batch mode
    else:
        repos = [
            ('Netflix', 'Hystrix'),        # Java
            ('mizzy', 'serverspec'),       # Ruby
            ('yiisoft' ,'yii'),            # PHP
            ('jashkenas' ,'backbone'),     # JavaScript
            ('Pylons' ,'pyramid'),         # Python
        ]
        repos = [
            ('Netflix', 'Hystrix'),        # Java
            ('mizzy', 'serverspec'),       # Ruby
            ('jashkenas' ,'backbone'),     # JavaScript
            ('yiisoft' ,'yii'),            # PHP

        ]

        for owner, repo in repos:
            run_pipeline(owner, repo)


if __name__ == "__main__":
    main()
