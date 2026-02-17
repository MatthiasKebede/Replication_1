"""
Data Collection Script (Step 1)

Collect the initial PR information using the GitHub API.

Usage:
    python mine_repo.py <owner> <repo>

Example:
    python mine_repo.py Yelp mrjob
"""

import sys
import os
import csv
from dotenv import load_dotenv
from github import Github
from github import Auth


# Load environment variables from .env file
load_dotenv()


def collect_pull_requests(owner: str, repo_name: str) -> None:
    """
    Mine repository data from GitHub.

    Args:
        owner: Repository owner (e.g., 'Yelp')
        repo: Repository name (e.g., 'mrjob')
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
    repo = git.get_repo(f"{owner}/{repo_name}")

    print(f"\n{'=' * 60}")
    print(f"REPOSITORY MINING RESULTS: {owner}/{repo_name}")
    print(f"{'=' * 60}\n")

    # File handling for CSV output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mined_output_dir = os.path.join(script_dir, '..', 'outputs', 'mined') # moved this to /mined subfolder
    os.makedirs(mined_output_dir, exist_ok=True)
    output_file = os.path.join(mined_output_dir, f'{repo_name}_pulls_raw.csv') # currently makes a CSV per repo, could combine into one
    
    # Collect PR information & metadata
    pull_requests = repo.get_pulls(state='all')
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        fields = [
            "author","pull_number","title","description","churn","changed_files","activities",
            "comments","comment_dates","state","creation_date","close_date","closed_by", "merged_at"
        ]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        
        for pr in pull_requests:
            # Get comment dates
            issue_comments = pr.get_issue_comments()
            review_comments = pr.get_review_comments()
            comment_dates = [
                c.created_at.isoformat() for c in issue_comments] + [
                c.created_at.isoformat() for c in review_comments]

            # PRs can have `merged_by` but not `closed_by`, issues do have it
            closed_by = None
            if pr.merged:
                closed_by = pr.merged_by
            elif pr.state == 'closed':
                issue = pr.as_issue()
                closed_by = issue.closed_by

            row = {
                "author": pr.user.login if pr.user else None,
                "pull_number": pr.number,
                "title": pr.title,
                "description": len(pr.body) if pr.body else 0, # pr.body,
                "churn": pr.additions + pr.deletions, # "number of added lines plus the number of deleted lines to a pull request"
                "changed_files": pr.changed_files,
                "activities": pr.get_issue_events().totalCount, # "an entry in the pull request' history"
                "comments": pr.comments + pr.review_comments, # counts normal/review comments, but not the initial description 'comment'
                "comment_dates": ";".join(comment_dates), # not clear how this is supposed to be handled
                "state": "merged" if pr.merged else pr.state, # tried to account for merged here
                "creation_date": pr.created_at.isoformat(), # ISO for consistency w/ comment dates
                "close_date": pr.closed_at if pr.closed_at else None,
                "closed_by": closed_by.login if closed_by else None,
                "merged_at": pr.merged_at if pr.merged else None
            }
            writer.writerow(row)
        
    git.close()

    print(f"Total Pull Requests: {pull_requests.totalCount}")
    print(f"\n{'=' * 60}\n")


def main():
    """Main entry point for the script"""
    if len(sys.argv) != 3:
        print("Usage: python mine_repo.py <owner> <repo>")
        print("Example: python mine_repo.py Yelp mrjob")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]

    collect_pull_requests(owner, repo)


if __name__ == "__main__":
    main()
