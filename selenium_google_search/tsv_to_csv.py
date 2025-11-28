import pandas as pd

# 1. Định nghĩa tên cột theo đúng README
column_names = [
    "id",                       # Column 1: ID of the statement
    "label",                    # Column 2: label
    "statement",                # Column 3: statement
    "subjects",                 # Column 4: subject(s)
    "speaker",                  # Column 5: speaker
    "speaker_job_title",        # Column 6: speaker's job title
    "state_info",               # Column 7: state info
    "party_affiliation",        # Column 8: party affiliation
    "barely_true_counts",       # Column 9
    "false_counts",             # Column 10
    "half_true_counts",         # Column 11
    "mostly_true_counts",       # Column 12
    "pants_on_fire_counts",     # Column 13
    "context"                   # Column 14: context
]

# 2. Đọc file .tsv
df = pd.read_csv(
    "test.tsv",          
    sep="\t",             
    header=None,          
    names=column_names,   
    encoding="utf-8"      
)

# 3. Ghi ra file .csv
df.to_csv("test.csv", index=False)
