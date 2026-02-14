## Notes:
- Conducted search on Feb 14th
- PR data collection says it collects the author, PR title, PR state, and closedBy (user) but these are not shown in the provided dataset. Also, a few other fields like `creation date` and `close date` are not directly shown, but might have been converted to values like `merge_time`.
- ^ Need to rewrite PR collection script to get 'raw' data and then produce the dataset after both collection steps.
- The raw PR collection does not include information like `pull_id` or `stacktrace_attached` that are referenced later on in the final dataset.
- Very little explanation of how things like `date_of_comments` should be handled before the explanatory model section.


## Assumptions:
- In Step 1 the attribute is called `description`, but it appears to only be used in the form of `description_length`. For our data collection we also store the description length instead of any text content.
- I was not entirely clear on the `activities` field despite the brief description, so I used the count given by the "issue events" API that uses the term similarly.
- Assuming that the comment count should include review comments, and that the PR description should not be counted even though the UI calls it a comment. Also, the corresponding comment dates are just stored as a sequence of ISO datetimes.

## Discrepancies:
