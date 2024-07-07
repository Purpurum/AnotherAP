import pandas as pd

df = pd.read_csv("subs1.csv")

dfs = {}
for number, group in df.groupby('name_folder'):
    dfs[number] = group

print(dfs[1])

