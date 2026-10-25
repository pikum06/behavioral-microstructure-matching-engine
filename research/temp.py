import pandas as pd

df = pd.read_csv('../outcomes/csv/cleaned_behavioral_profiles.csv')

print(df.shape)

print(df.columns.tolist())

print(df.head(10))