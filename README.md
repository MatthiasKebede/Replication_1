<p style="border:1px; border-style:solid; border-color:black; padding: 1em;">
CS-UH 3260 Software Analytics<br/>
Replication Study Guidelines<br/>
Dr. Sarah Nadi, NYUAD
</p>

# Replication 1 -- CS-UH-3260 Software Analytics


## Overview

This repo contains the scripts and data used for the `Replication 1` assignment, focusing on the paper *Studying the impact of adopting continuous integration on the delivery time of pull requests*. The scope of our replication includes RQ1 and RQ2, which relate to the merge time and delivery time of PRs in open-source repositories.


### 1. Project Title and Overview

- **Paper Title**: Studying the impact of adopting continuous integration on the delivery time of pull requests
- **Authors**: João Helis Bernardo, Daniel Alencar da Costa, and Uirá Kulesza
- **Replication Team**: Matthias Kebede and Muhammad Arhum
- **Course**: CS-UH 3260 Software Analytics, NYUAD
- **Brief Description**: 
  - In the original study, the authors mine PR and Release metadata from 87 open-source repositories that adopted Continuous Integration (specifically through `Travis-CI`). They use this data to identify trends in how PRs are merged and delivered through releases during the pre-CI and post-CI periods, with the end goal of determining whether CI definitively allows developers to deliver new functionalities in a shorter time frame.
  - Our replication study focuses on RQ1 and RQ2 of the paper. First we write analysis scripts according to the descriptions in the paper and run them against the provided dataset, which allows us to verify that our scripts return accurate results. Then we write additional scripts to handle mining updated data from 5 repositories out of the original selection and compare our computed results of RQ1 (using the new data) against the published figures.

### 2. Repository Structure

Document your repository structure clearly. Organize your repository using the following standard structure:

```
README                                     # Documentation for your repository
datasets/                                  # Original datasets provided by the authors (https://prdeliverydelay.github.io/)
  - pull_requests_meta_data.csv                # provided metadata of all PRs
  - releases_meta_data.csv                     # provided metadata of all releases
  - wilcoxon_test...for_rq1.csv                # provided statistical analysis results for RQ1
replication_scripts/                       # Scripts used in your replication:
  - collect_pulls.py                           # mines PR data from specified repo
  - collect_releases.py                        # mines release data from specified repo (also links PRs to releases)
  - merge.py                                   # combines PR and release data into one CSV
  - metrics.py                                 # performs statistical analysis
  - run.py                                     # orchestrates data collection + processing process
  - test.py                                    # compares analysis results of mined vs provided data
outputs/                                   # Your generated results only
  mined/                                       # Output from mining scripts
    - <repo>_pulls_raw.csv                         # contains mined PR data for a specific repo
    - <repo>_releases_raw.csv                      # contains mined release data for a specific repo
    - <repo>_releases_linked.csv                   # simple two-column CSV linking PRs to releases
    - <repo>_data_merged.csv                       # same as raw PR data but adds release_tag field
  - results_from_original_data.csv             # output of statistical analysis run on provided dataset
logs/                                      # Console output, errors, screenshots
notes/                                     # Optional if you have any notes you took during reproduction (E.g., where you noted discrepencies etc)
  - notes.md                                   # contains general notes, assumptions, and discrepancies
```

**For each folder and file, provide a brief description of what it contains.**

### 3. Setup Instructions

- **Prerequisites**:
  - Python 3.11 or higher
  - Git and Pip are installed (tested with `git version 2.41.0.windows.1` and `pip 23.1.2`)
- **Installation Steps**: Step-by-step instructions to set up the environment
  - Clone the repository (e.g. `git clone https://github.com/MatthiasKebede/Replication_1`) and navigate to the directory
  - Create a virtual environment and activate it, then install required libraries:
  ```bash
  python -m venv .venv                   # create venv
  source .venv/bin/activate              # activate venv (`.venv/scripts/activate` on Windows)
  pip install -r requirements.txt        # install libraries
  ```
  - Create a `.env` file and paste in your GitHub Personal Access Token (e.g. `GITHUB_TOKEN=sample_token_value`) and Travis-CI API Token (e.g. `TRAVIS_TOKEN=sample_token`)
- **Running Instructions**:
  - (explain `run.py` here once it is finalized)
  - **Collecting New Data**:
    - Collect PR metadata for a given repository by running `python collect_pulls.py <owner> <repo>` (will take a long time for repos w/ many PRs)
    - Collect release metadata for a given repo by running `python collect_releases.py <owner> <repo>`. This works locally instead of using the GitHub API, so you can optionally clone the specified repo beforehand (looks for sibling directory `Replication_1/../temp_repos/<repo>` by default). Otherwise, it will automatically clone the repo to that location.
  - **Analyzing Data**:
    - Run the statistical analysis using `python metrics.py`. By default this will run on the set of repositories listed in `mine_suite2` under the main function. You can also opt to analyze the author's provided dataset by uncommenting the code block at the bottom of the file.
    - After running the statistical analysis, you can run `python test.py` to compare the results computed from the mined vs provided data (assuming you have run the `metrics.py` script with the mentioned code block uncommented).

### 4. GenAI Usage
<!-- **GenAI Usage**: Briefly document any use of generative AI tools (e.g., ChatGPT, GitHub Copilot, Cursor) during the replication process. Include:
  - Which tools were used
  - How they were used (e.g., understanding scripts, exploring datasets, understanding data fields, debugging)
  - Brief description of the assistance provided -->

  - **GitHub Copilot**
    - Used to improve file handling for CSVs and to help identify which `PyGithub` PR attributes correspond to the fields needed in the initial `collect_pulls.py` script.
    - Also to help switch usage from `pydriller` to `GitPython` and use regex while working on the `collect_releases.py` script.
  - **ChatGPT**
    - Helped with figuring out how to format the LaTeX tables in the report.


## Grading Criteria for README

Your README will be evaluated based on the following aspects (Total: 40 points):

### 1. Completeness (10 points)
- [ ] All required sections are present
- [ ] Each section contains sufficient detail
- [ ] Repository structure is fully documented
- [ ] All files and folders are explained
- [ ] GenAI usage is documented (if any AI tools were used)

### 2. Clarity and Organization (5 points)
- [ ] Information is well-organized and easy to follow
- [ ] Instructions are clear and unambiguous
- [ ] Professional writing and formatting
- [ ] Proper use of markdown formatting (headers, code blocks, lists)

### 3. Setup and Reproducibility (10 points)
- [ ] Setup instructions are complete and accurate, i.e., we were able to rerun the scripts following your instructions and obtain the results you reported


## Best Practices

1. **Be Specific**: Include exact versions, paths, and commands rather than vague descriptions
2. **Keep It Updated**: Ensure the README reflects the current state of your repository
3. **Test Your Instructions**: Have someone else (or yourself in a fresh environment) follow the setup instructions
4. **Document AI Usage**: If you used any GenAI tools, be transparent about how they were used (e.g., understanding scripts, exploring datasets, understanding data fields)


## Acknowledgement

This guideline was developed with the assistance of [Cursor](https://www.cursor.com/), an AI-powered code editor. This tool was used to:

- Draft and refine this documentation iteratively
