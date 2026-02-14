"""
Data Collection Script

This script mines GitHub repository data using the GitHub API.

Usage:
    python mine_repo.py <owner> <repo>

Example:
    python mine_repo.py psf requests
"""

import sys
import os
import csv
from dotenv import load_dotenv
from github import Github
from github import Auth


# Load environment variables from .env file
load_dotenv()


def mine_repository(owner: str, repo: str) -> None:
    """
    Mine repository data from GitHub.

    Args:
        owner: Repository owner (e.g., 'psf')
        repo: Repository name (e.g., 'requests')
    """
    # Get GitHub token from environment
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found in .env file")
        print("Please create a .env file with your GitHub token:")
        print("GITHUB_TOKEN=your_token_here")
        sys.exit(1)

    # Initialize GitHub API client here
    auth = Auth.Token(token)
    git = Github(auth=auth)
    repo = git.get_repo(f"{owner}/{repo}")

    print(f"\n{'=' * 60}")
    print(f"REPOSITORY MINING RESULTS: {owner}/{repo}")
    print(f"{'=' * 60}\n")
    
    # Collect PR information & metadata
    pull_requests = repo.get_pulls(state='all')
    with open('outputs/pull_requests.csv', 'w', newline='') as file:
        fields = [
                "","X.","project","language","pull_id","pull_number","commits_per_pr",
                "changed_files","churn","comments","comments_interval","merge_workload",
                "description_length","contributor_experience","queue_rank","contributor_integration",
                "stacktrace_attached","activities","merge_time","delivery_time","practice"
            ]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        
        i = 0
        for pr in pull_requests:
            i += 1
            row = {
                "": i,
                "X.": i,
                "project": repo.full_name,   # Full name of the GitHub repository
                "language": repo.language,   # Programming language used by the project
                "pull_id": pr.id,   # Pull request ID
                "pull_number": pr.number,   # Pull request number
                "commits_per_pr": pr.commits,   # Number of commits per PR
                "changed_files": pr.changed_files,   # The number of files linked to a pull request submission
                "churn": pr.additions + pr.deletions,   # The number of added lines plus the number of deleted lines to a pull request
                "comments": pr.comments,   # The number of comments of a pull request
                # "comments_interval": ,   # The sum of the time intervals (days) between comments divided by the total number of comments of a pull request
                # "merge_workload": ,   # The amount of PR that were created and still waiting to be merged by a core integrator at the moment at which a specific pull request is submitted
                "description_length": len(pr.body) if pr.body else 0,   # The number of characters in the body (description) of the PR
                # "contributor_experience": ,   # The number of previously released pull requests that were submitted by the contributor of a particular PR. We consider the author of the pull request to be its contributor
                # "queue_rank": ,   # The number that represents the moment when a pull request is merged compared to other merged PRs in the release cycle. For example, in a queue that contains 100 PRs, the first merged PR has position 1, while the last merged pull request has position 100
                # "contributor_integration": ,   # The average in days of the previously released PRs that were submitted by a particular contributor
                # "stacktrace_attached": ,   # We verify whether the pull request report has an stack trace attached in its description
                # "activities": ,   # An activity is an entry in the pull request' history
                # "merge_time": ,   # Number of days between the submission and merge of a pull request
                # "delivery_time": ,   # Number of days between the merge and the delivery of a pull request
                # "practice": # We verify whether a pull request was submitted before or after the adoption of CI
            }
            writer.writerow(row)
        
    git.close()

    print("Repository Info:")
    print(f"- Total Pull Requests: {pull_requests.totalCount}")

    print(f"\n{'=' * 60}\n")


def main():
    """Main entry point for the script."""
    if len(sys.argv) != 3:
        print("Usage: python mine_repo.py <owner> <repo>")
        print("Example: python mine_repo.py psf requests")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]

    mine_repository(owner, repo)


if __name__ == "__main__":
    main()
