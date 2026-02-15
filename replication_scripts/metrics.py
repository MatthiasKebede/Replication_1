
import pandas as pd
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
import requests
from scipy.stats import mannwhitneyu
from cliffs_delta import cliffs_delta






load_dotenv()

def analyze_ci_data(before_ci: pd.DataFrame, after_ci: pd.DataFrame, repo, out_file: str):
    """
    Compute MWW and Cliff's delta for delivery delay (t2), merge time (t1), and PR lifetime.
    If output file exists:
        - Update row if repo already exists
        - Otherwise append new row
    """

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
        if delta is None:
            return ""
        abs_delta = abs(delta)
        if abs_delta < 0.147:
            return "negligible"
        elif abs_delta < 0.33:
            return "small"
        elif abs_delta < 0.474:
            return "medium"
        else:
            return "large"

    #decimal formatting
    def fmt(x):
        if x is None:
            return ""
        return format(float(x), ".10f")  

    row = {
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
            p_value, delta, magnitude = None, None, None

        row[f"Cliff delta (magnitude): {metric_name}"] = magnitude
        row[f"Cliff delta (estimate): {metric_name}"] = fmt(delta)
        row[f"MWW test (p-value): {metric_name}"] = fmt(p_value)

    new_row_df = pd.DataFrame([row])

    if os.path.exists(out_file):
        existing_df = pd.read_csv(out_file)

        if repo in existing_df["project"].values:
            # Update the existing row safely
            existing_row_idx = existing_df[existing_df["project"] == repo].index[0]
            for column in new_row_df.columns:
                # Convert any string (even scientific notation) to float before assignment
                value = new_row_df[column].iloc[0]
                if isinstance(value, str):  # Check if it's a string
                    try:
                        # Convert the string to a float if possible
                        value = float(value)
                    except ValueError:
                        pass  # If it can't be converted, leave it as is

                existing_df.at[existing_row_idx, column] = value
        else:
            # Append new row if repo not in the file
            existing_df = pd.concat([existing_df, new_row_df], ignore_index=True)

        # Save back to CSV
        existing_df.to_csv(out_file, index=False)
    else:
        # File doesn't exist → create new
        new_row_df.to_csv(out_file, index=False)

    print(f"Results saved/updated in {out_file}")



def first_CI(owner,repo_name):

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
                return pd.to_datetime(ci_start_date)  # Convert to datetime
                
            else:
                print("No builds found.")
                return
                
        else:
            print("Failed to fetch data from Travis API.")
            return
                
    except Exception as e:
        print(f"Error fetching data: {e}")
        return





def statistics(repo_name, owner):
    
    # Reading release and pull request data
    ci_start_date = first_CI(owner, repo_name)
    if ci_start_date == None:
        print("CI start date not found, Run first_CI on the repo/s to check")
        return
    release_data_raw = pd.read_csv(f"../outputs/{repo_name}_releases_raw.csv")
    release_data_link = pd.read_csv(f"../outputs/{repo_name}_releases_linked.csv")

    # Rename title -> release_tag
    release_data = release_data_raw.rename(columns={'title': 'release_tag'})

    # Merge using the renamed DataFrame
    release_df = pd.merge(
        release_data_link,  # has pull_number, release_tag
        release_data,       # has release_tag, publish_date, start_date, etc.
        on='release_tag',   # merge using release_tag
        how='left'          # keep all PRs
    )

    # Keep only the columns you want
    release = release_df[['pull_number', 'release_tag', 'publish_date', 'start_date']]
    release = release.rename(columns={'pull_number': 'pull_number'})

    
    pull_data = pd.read_csv(f"../outputs/{owner}_{repo_name}_pulls_raw.csv")

    # Merging release and pull data
    data = pd.merge(release_df[['pull_number', 'release_tag', 'publish_date', 'start_date']],
                    pull_data[["pull_number", "creation_date", "close_date", "merged_at"]],
                    left_on='pull_number',
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
    #print("Before CI")
    #print(before_ci[['pull_number', 't1', 't2', 'lifetime']])
    
    #print("After CI")
    #print(after_ci[['pull_number', 't1', 't2', 'lifetime']])
    delivery_time = "t2"
    stat, p_value = mannwhitneyu(before_ci[delivery_time], after_ci[delivery_time], alternative='two-sided')
    #print("MWW p-value:", p_value)
    delta, res = cliffs_delta(before_ci[delivery_time], after_ci[delivery_time])
    #print("Cliff's delta:", delta, res)
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
    test_suite1 = [
                ('yiisoft' ,'yii'),
                ('vanilla' ,'vanilla'),
                ('scikit-image' ,'scikit-image'),
                ('dropwizard' ,'dropwizard'),
                ('androidannotations' ,'androidannotations'),
                ('jashkenas' ,'backbone'),
                ('bcit-ci' ,'CodeIgniter'),
                ('mizzy' ,'serverspec'),
                ('ReactiveX' ,'RxJava'),
                ('Netflix' ,'Hystrix'),
                ('refinery' ,'refinerycms'),
                ('Pylons' ,'pyramid'),
                ('ether' ,'etherpad-lite'),
                ('jashkenas' ,'underscore'),
                ('BabylonJS' ,'Babylon.js'),
                ('loomio' ,'loomio'),
                ('scikit-learn' ,'scikit-learn'),
                ('puppetlabs' ,'puppet'),
                ('woocommerce' ,'woocommerce'),
                ('scipy' ,'scipy'),
                ('matplotlib' ,'matplotlib'),
                ('ipython' ,'ipython')
        ]
    test_suite2 = [
        ('Netflix', 'Hystrix'),
        ('mizzy', 'serverspec'),
        ('roots', 'sage'),
        ('spark', 'notebook'),
        ('yelp', 'mrjob'),
    ]
    for owner, repo in test_suite2:
        try:
            before_ci, after_ci =  statistics(repo, owner)
            analyze_ci_data(before_ci, after_ci, repo,"../outputs/results.csv")
            #first_CI(owner, repo)
        except:
            continue
if __name__ == "__main__":
    main()