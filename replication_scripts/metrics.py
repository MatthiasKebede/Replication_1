
import pandas as pd
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
import requests
from scipy.stats import mannwhitneyu
from cliffs_delta import cliffs_delta






load_dotenv()



def dataSetup_from_original_datasets(pull_csv_path: str, release_csv_path: str):
    """
    Load the original authors' datasets and return a list of:
    
        (repo_name, before_ci_df, after_ci_df)

    Each DataFrame contains:
        - t1 (merge_time)
        - t2 (delivery_time)
        - lifetime
    Compatible with analysis().
    """

    import pandas as pd

    # --------------------------------------------------
    # Load datasets
    # --------------------------------------------------
    pr_data = pd.read_csv(pull_csv_path)
    release_data = pd.read_csv(release_csv_path)  # not required for metrics

    # --------------------------------------------------
    # Clean numeric columns
    # --------------------------------------------------
    pr_data["merge_time"] = pd.to_numeric(pr_data["merge_time"], errors="coerce")
    pr_data["delivery_time"] = pd.to_numeric(pr_data["delivery_time"], errors="coerce")

    # --------------------------------------------------
    # Create expected metric columns
    # --------------------------------------------------
    pr_data["t1"] = pr_data["merge_time"]
    pr_data["t2"] = pr_data["delivery_time"]
    pr_data["lifetime"] = pr_data["t1"] + pr_data["t2"]

    results = []

    # --------------------------------------------------
    # Process each repository separately
    # --------------------------------------------------
    for project_name, group in pr_data.groupby("project"):

        before_ci = group[group["practice"] != "CI"].copy()
        after_ci = group[group["practice"] == "CI"].copy()

        # Remove missing values
        before_ci = before_ci.dropna(subset=["t1", "t2", "lifetime"])
        after_ci = after_ci.dropna(subset=["t1", "t2", "lifetime"])

        # Only include repos with both groups
        if len(before_ci) == 0 or len(after_ci) == 0:
            print(f"Skipping {project_name}: insufficient before/after data.")
            continue

        results.append((project_name, before_ci, after_ci))

    return results


def transform_to_metric_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms a single-row wide results DataFrame into a
    metric-wise horizontal summary table.

    Assumes df contains exactly one row.
    """

    if len(df) != 1:
        raise ValueError("DataFrame must contain exactly one row.")

    row = df.iloc[0]

    metrics = ["delivery delay", "merge time", "PR lifetime"]

    rows = []

    for metric in metrics:
        rows.append({
            "Metric": metric.title(),
            "Cliff Magnitude": row[f"Cliff delta (magnitude): {metric}"],
            "Cliff Estimate": row[f"Cliff delta (estimate): {metric}"],
            "MWW p-value": row[f"MWW test (p-value): {metric}"]
        })

    return pd.DataFrame(rows)


def analysis(before_ci: pd.DataFrame, after_ci: pd.DataFrame, repo, out_file: str):
    """
    Compute MWW and Cliff's delta for delivery delay (t2), merge time (t1), and PR lifetime.
    """

    # Ensure necessary columns exist (e.g., t1, t2, lifetime)
    for df in [before_ci, after_ci]:
        if "t1" not in df.columns or "t2" not in df.columns or "lifetime" not in df.columns:
            print("Did not get the required information")
            return

    metrics = {
        "delivery delay": "t2",
        "merge time": "t1",
        "PR lifetime": "lifetime"
    }
    #Labeling as per the paper
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

    # Decimal formatting function for output
    def fmt(x):
        if x is None:
            return ""
        return format(float(x), ".10f")

    # Row for the current repo
    row = {
        "project": repo
    }

    # Track number of significant results for summary
    significant_results = {
        "delivery delay": 0,
        "merge time": 0,
        "PR lifetime": 0
    }

    for metric_name, col in metrics.items():
        before_values = before_ci[col].dropna() #dropna removes missing values Removes missing values
        after_values = after_ci[col].dropna()   # stat function can't handle them

        if len(before_values) > 0 and len(after_values) > 0:
            stat, p_value = mannwhitneyu(before_values, after_values, alternative='two-sided')
            delta, _ = cliffs_delta(after_values, before_values) # idk why but this need to be reversed to mathc signs with the orginal ouptus
            magnitude = cliff_magnitude(delta)
            
            # Track significant p-values
            if p_value < 0.05:
                significant_results[metric_name] += 1
        else:
            p_value, delta, magnitude = None, None, None

        row[f"Cliff delta (magnitude): {metric_name}"] = magnitude
        row[f"Cliff delta (estimate): {metric_name}"] = fmt(delta)
        row[f"MWW test (p-value): {metric_name}"] = fmt(p_value)

    # Create DataFrame with the results
    new_row_df = pd.DataFrame([row])
    if out_file == '':
        print(repo)
        print(transform_to_metric_table(new_row_df))
        return
    # Update or append to the output CSV file
    if os.path.exists(out_file):
        existing_df = pd.read_csv(out_file)

        if repo in existing_df["project"].values:
            # Update the existing row
            existing_row_idx = existing_df[existing_df["project"] == repo].index[0]
            for column in new_row_df.columns:
                value = new_row_df[column].iloc[0]
                if isinstance(value, str):  # Check if it's a string
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # Leave it as is if conversion fails

                existing_df.at[existing_row_idx, column] = value
        else:
            # Append new row if repo not in the file
            existing_df = pd.concat([existing_df, new_row_df], ignore_index=True)

        # Save the updated DataFrame back to CSV
        existing_df.to_csv(out_file, index=False)
    else:
        # File doesn't exist → create new one
        new_row_df.to_csv(out_file, index=False)

    print(f"Results saved/updated in {out_file}")

def first_CI_by_TRAVIS_API(owner,repo_name):

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





def dataSetup(repo_name, owner):
    
    # Reading release and pull request data
    ci_start_date = first_CI_by_TRAVIS_API(owner, repo_name)
    if ci_start_date == None:
        print("CI start date not found, Run first_CI_by_TRAVIS_API on the repo/s to check")
        return
    try:
        release_data_raw = pd.read_csv(f"../outputs/{repo_name}_releases_raw.csv")
        release_data_link = pd.read_csv(f"../outputs/{repo_name}_releases_linked.csv")
    except:
        print("If file does not exit, run collect_pull.py and collect_release.py for this repo then try again")
        return
    # Rename title -> release_tag
    release_data = release_data_raw.rename(columns={'title': 'release_tag'})

    # Merge using the renamed DataFrame
    release_df = pd.merge(
        release_data_link,  # has pull_number, release_tag
        release_data,       # has release_tag, publish_date, start_date, etc.
        on='release_tag',   # merge using release_tag
        how='left'          # keep all PRs
    )

    # Keep only required columns
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

    return before_ci, after_ci

def main():
    #Main entry point for the script
    #1
    #if you want results for all the repos we minned, or form the data provided by Authors comment this and scroll down to #2 or #3
    """ if len(sys.argv) != 3:
        print("Usage: python mine_repo.py <repo> <owner>")
        print("Example: python mine_repo.py mrjob Yelp")
        sys.exit(1)

    repo = sys.argv[1]
    owner = sys.argv[2]
    before_ci, after_ci =  dataSetup(repo, owner)
    analysis(before_ci, after_ci, repo,"")"""
    #Travis CI API Authentication was availble for following repos in mine_suite1
    mine_suite1 = [
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
    #repos we minned
    mine_suite2 = [
        ('Netflix', 'Hystrix'),
        ('mizzy', 'serverspec'),
        ('roots', 'sage'),
        ('spark', 'notebook'),
        ('yelp', 'mrjob'),
    ]
    #2
    # Uncomment the below code to run analysis on the the data we minned form repos listed in mine_suite2, it will be save in a file called ../outputs/results_from_minned_data.csv
   
    for owner, repo in mine_suite2:
        try:
            before_ci, after_ci =  dataSetup(repo, owner)
            analysis(before_ci, after_ci, repo,"../outputs/results_from_minned_data.csv")
            #first_CI_by_TRAVIS_API(owner, repo)
        except:
            continue
   
    #3
    # Uncoment the below code to run the analysis on the Author's dataset, the output will be in a called ../outputs/results_from_orignal_data.csv
    """

    x = dataSetup_from_original_datasets('../datasets/pull_requests_meta_data.csv','../datasets/releases_meta_data.csv')
    for r, b ,c in x:
        analysis(b,c,r,"../outputs/results_from_orignal_data.csv" )
    """
if __name__ == "__main__":
    main()