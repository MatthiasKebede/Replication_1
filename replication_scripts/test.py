
"""
This file is created to match verify the analysis of our code with the analysis of the authors. It will create a 
csv file in current dir, containing outputs for manual analysis
"""



import pandas as pd
import re
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
calculated_file = os.path.join(script_dir, '..', 'outputs', 'results_from_orignal_data.csv')
dataset_file = os.path.join(script_dir, '..', 'datasets', 'wilcoxon_test_and_cliffs_delta_result_for_rq1.csv')
combined_file = os.path.join(script_dir, '..', 'outputs', 'comparison_combined_results.csv')


def merge_projects_both_files(your_file, authors_file, output_combined_file):
    # --------------------------------------------------
    # 1️⃣ Read CSVs
    # --------------------------------------------------
    your_df = pd.read_csv(your_file)
    authors_df = pd.read_csv(authors_file)

    # --------------------------------------------------
    # 2️⃣ Normalize column names (lowercase, replace underscores/hyphens, strip)
    # --------------------------------------------------
    def normalize_cols(cols):
        return [re.sub(r'[\s_-]+', ' ', col.strip().lower()) for col in cols]

    your_df.columns = normalize_cols(your_df.columns)
    authors_df.columns = normalize_cols(authors_df.columns)

    # Normalize project column
    your_df["project"] = your_df["project"].astype(str).str.strip().str.lower()
    authors_df["project"] = authors_df["project"].astype(str).str.strip().str.lower()

    # Drop empty projects
    your_df = your_df[your_df["project"].notna() & (your_df["project"] != "nan")]
    authors_df = authors_df[authors_df["project"].notna() & (authors_df["project"] != "nan")]

    # --------------------------------------------------
    # 3️⃣ Identify common projects
    # --------------------------------------------------
    common_projects = set(your_df["project"]).intersection(set(authors_df["project"]))
    if not common_projects:
        print("⚠ No common projects found between files.")
        return

    # --------------------------------------------------
    # 4️⃣ Get the unique columns from both files
    # --------------------------------------------------
    your_columns = set(your_df.columns)
    authors_columns = set(authors_df.columns)

    # Columns that exist in authors file but not in yours
    missing_columns = authors_columns - your_columns

    # Create a column for each of the missing columns in your file, filled with NaN
    for col in missing_columns:
        your_df[col] = pd.NA  # Add these missing columns to your DataFrame

    # --------------------------------------------------
    # 5️⃣ Merge the rows for each project, from both files
    # --------------------------------------------------
    combined_rows = []

    for project in sorted(common_projects):
        # Get rows for the project from both DataFrames
        y_row = your_df[your_df["project"] == project].iloc[0]
        a_row = authors_df[authors_df["project"] == project].iloc[0]

        # Add your row first
        combined_row_your = y_row.copy()
        combined_row_your["source"] = "your_file"
        combined_rows.append(combined_row_your)

        # Add author's row second
        combined_row_author = a_row.copy()
        combined_row_author["source"] = "author_file"
        combined_rows.append(combined_row_author)

    # --------------------------------------------------
    # 6️⃣ Reorganize results for saving (Just the relevant columns)
    # --------------------------------------------------
    # Make sure 'project' is the first column, followed by the rest of the columns in the order of your file.
    final_columns = ["source", "project"] + list(your_columns - {"project"})

    final_df = pd.DataFrame(combined_rows, columns=final_columns)

    # --------------------------------------------------
    # 7️⃣ Save the results to a CSV file
    # --------------------------------------------------
    final_df.to_csv(output_combined_file, index=False)
    print(f"Comparison results saved in {output_combined_file}")

# Example usage
#merge_projects_both_files(calculated_file, dataset_file, combined_file)
calculated_file = os.path.join(script_dir, '..', 'outputs',  'results_from_minned_data.csv')
dataset_file = os.path.join(script_dir, '..', 'datasets', 'wilcoxon_test_and_cliffs_delta_result_for_rq1.csv')
combined_file = os.path.join(script_dir, '..', 'outputs', 'comparison_combined_results.csv')



merge_projects_both_files(calculated_file, dataset_file, combined_file)