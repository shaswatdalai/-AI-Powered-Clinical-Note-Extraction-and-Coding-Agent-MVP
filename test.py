import pandas as pd

# Clinical notes
notes = pd.read_csv("mtsamples.csv")
print(notes.shape)
print(notes.columns.tolist())

# ICD-10
icd = pd.read_csv("icd10cm_data.csv")
print(icd.shape)
print(icd.columns.tolist())