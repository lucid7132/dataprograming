import pandas as pd
import os
import shutil

data_path = "data/price_at"
os.makedirs(data_path, exist_ok=True)

items = ['무', '깐마늘', '양파', '사과', '배추']

for item in items:
    files_to_move = [f"{item}.csv", f"{item}19.csv"]
    for file_name in files_to_move:
        if os.path.exists(file_name):
            shutil.move(file_name, os.path.join(data_path, file_name))

dfs = []

for item in items:
    file_recent = os.path.join(data_path, f"{item}.csv")
    file_old = os.path.join(data_path, f"{item}19.csv")
    df_recent = pd.read_csv(file_recent)
    df_old = pd.read_csv(file_old)

    df_recent = df_recent[['Category', '평균']]
    df_old = df_old[['Category', '평균']]
    
    df_item = pd.concat([df_old, df_recent])
    
    df_item.rename(columns={'평균': item}, inplace=True)
    df_item.set_index('Category', inplace=True)
    dfs.append(df_item)

total_df = pd.concat(dfs, axis=1)
total_df.sort_index(inplace=True)
total_df.to_csv('at_processing_data.csv')

print(total_df.head())
print(total_df.info())