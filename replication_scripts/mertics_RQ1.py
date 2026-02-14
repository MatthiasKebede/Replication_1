
import pandas as pd
import sys
from github import Github, Auth
import os
from datetime import datetime
from dotenv import load_dotenv
import requests
from scipy.stats import mannwhitneyu
from cliffs_delta import cliffs_delta





def analyze_ci_data(before_ci: pd.DataFrame, after_ci: pd.DataFrame,repo, out_file: str):
    """
    Compute MWW and Cliff's delta for delivery delay (t2), merge time (t1), and PR lifetime,
    and save the results in the authors’ CSV format.

    Parameters:
        before_ci (pd.DataFrame): PR data before CI
        after_ci (pd.DataFrame): PR data after CI
        project_name (str): Name of the project, e.g., "Yelp/mrjob"
        out_file (str): Path to save the output CSV
    """


    # Ensure t1, t2, lifetime columns exist
    for df in [before_ci, after_ci]:
        if "t1" not in df.columns:
            df["t1"] = (df['merged_at'] - df['creation_date']).dt.total_seconds()
        if "t2" not in df.columns:
            df["t2"] = (df['publish_date'] - df['merged_at']).dt.total_seconds()
        if "lifetime" not in df.columns:
            df["lifetime"] = df["t1"] + df["t2"]

    metrics = {
        "delivery delay": "t2",
        "merge time": "t1",
        "PR lifetime": "lifetime"
    }

    def cliff_magnitude(delta):
        abs_delta = abs(delta)
        if abs_delta < 0.147:
            return "negligible"
        elif abs_delta < 0.33:
            return "small"
        elif abs_delta < 0.474:
            return "medium"
        else:
            return "large"

    # Format numbers with comma as decimal separator
    def fmt(x):
        if x is None:
            return ""
        return str(round(x, 9)).replace(".", ",")

    row = {
        "#": 1,
        "project": repo
    }

    for metric_name, col in metrics.items():
        before_values = before_ci[col].dropna()
        after_values = after_ci[col].dropna()

        if len(before_values) > 0 and len(after_values) > 0:
            stat, p_value = mannwhitneyu(before_values, after_values, alternative='two-sided')
            delta, _ = cliffs_delta(before_values, after_values)
            magnitude = cliff_magnitude(delta)
        else:
            stat, p_value, delta, magnitude = None, None, None, None

        row[f"Cliff delta (magnitude): {metric_name}"] = magnitude
        row[f"Cliff delta (estimate): {metric_name}"] = fmt(delta)
        row[f"MWW test (p-value): {metric_name}"] = fmt(p_value)

    # Convert to DataFrame and save
    output_df = pd.DataFrame([row])
    output_df.to_csv(out_file, index=False)
    print(f"CSV saved to {out_file}")






load_dotenv()

def statistics(repo_name, owner):
    # Travis API URL and setup
    api_url = "https://api.travis-ci.com"
    repo_slug = f"{owner}/{repo_name}"  # Ensure the correct order: owner/repo
    repo_slug_encoded = repo_slug.replace("/", "%2F")
    travis_token = os.getenv("TRAVIS_TOKEN")
    headers = {
        "Travis-API-Version": "3",
        "Authorization": f"token {travis_token}"
    }

    # Make the API request to Travis
    url = f"{api_url}/repo/{repo_slug_encoded}/builds?limit=1&sort_by=started_at:asc"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            builds = response.json()["builds"]
            if builds:
                first_build = builds[0]
                ci_start_date = first_build["started_at"]
                print("CI start date detected via Travis API:", ci_start_date)
                ci_start_date = pd.to_datetime(ci_start_date)  # Convert to datetime
                
            else:
                print("No builds found.")
                return
                
        else:
            print("Failed to fetch data from Travis API.")
            return
                
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Reading release and pull request data
    release_data = pd.read_csv(f"{repo_name}_releases_raw_for_timeline.csv")
    pull_data = pd.read_csv(f"{owner}_{repo_name}_pulls_raw.csv")

    # Merging release and pull data
    data = pd.merge(release_data[['pr_number', 'release_tag', 'publish_date', 'start_date']],
                    pull_data[["pull_number", "creation_date", "close_date", "merged_at"]],
                    left_on='pr_number',
                    right_on='pull_number',
                    how='inner')

    # Fixing datetime columns
    data['creation_date'] = pd.to_datetime(data['creation_date'], utc=True)
    data['merged_at'] = pd.to_datetime(data['merged_at'], utc=True)
    data['publish_date'] = pd.to_datetime(data['publish_date'], utc=True)
    data['start_date'] = pd.to_datetime(data['start_date'], utc=True)

    # Creating columns for t1, t2, and lifetime
    data["t1"] = (data['merged_at'] - data['creation_date']).dt.total_seconds()
    data["t2"] = (data['publish_date'] - data['merged_at']).dt.total_seconds()
    data["lifetime"] = data['t1'] + data['t2']

    # Create two DataFrames: before and after CI start date
    before_ci = data[data['creation_date'] < ci_start_date]
    after_ci = data[data['creation_date'] >= ci_start_date]

    # Printing the data
    print("Before CI")
    print(before_ci[['pr_number', 't1', 't2', 'lifetime']])
    
    print("After CI")
    print(after_ci[['pr_number', 't1', 't2', 'lifetime']])
    delivery_time = "t2"
    stat, p_value = mannwhitneyu(before_ci[delivery_time], after_ci[delivery_time], alternative='two-sided')
    print("MWW p-value:", p_value)
    delta, res = cliffs_delta(before_ci[delivery_time], after_ci[delivery_time])
    print("Cliff's delta:", delta, res)
    return before_ci, after_ci

def main():
    """Main entry point for the script
    if len(sys.argv) != 3:
        print("Usage: python mine_repo.py <repo> <owner>")
        print("Example: python mine_repo.py mrjob Yelp")
        sys.exit(1)

    repo = sys.argv[1]
    owner = sys.argv[2]"""
    """Main entry point for the script"""
    test_suite = [
        ('mizzy', 'serverspec'),
        ('vanilla', 'vanilla'),
        ('scikit-image', 'scikit-image'),
        ('dropwizard', 'dropwizard'),
        ('androidannotations', 'androidannotations'),
        ('jashkenas', 'backbone'),
        ('bcit-ci', 'CodeIgniter'),
        ('ReactiveX', 'RxJava'),
        ('Netflix', 'Hystrix'),
        ('refinery', 'refinerycms')
    ]
    for owner, repo in test_suite:
        before_ci, after_ci = statistics(repo, owner)
        analyze_ci_data(before_ci, after_ci, repo,"test1.csv")
        break

if __name__ == "__main__":
    main()
