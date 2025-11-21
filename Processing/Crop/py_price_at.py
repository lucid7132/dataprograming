import pandas as pd
import os
import shutil

# Create the directory structure requested by the user
data_path = "data/price_at"
os.makedirs(data_path, exist_ok=True)

# List of items
items = ['무', '깐마늘', '양파', '사과', '배추']

# Move the uploaded files to the requested directory to simulate the user's environment
# The files are currently in the root directory
for item in items:
    files_to_move = [f"{item}.csv", f"{item}19.csv"]
    for file_name in files_to_move:
        if os.path.exists(file_name):
            shutil.move(file_name, os.path.join(data_path, file_name))

# Now proceed with the data processing using the requested path
dfs = []

for item in items:
    # Define file paths using the data_path variable
    file_recent = os.path.join(data_path, f"{item}.csv")
    file_old = os.path.join(data_path, f"{item}19.csv")
    
    # Read CSVs
    df_recent = pd.read_csv(file_recent)
    df_old = pd.read_csv(file_old)
    
    # Select specific columns
    df_recent = df_recent[['Category', '평균']]
    df_old = df_old[['Category', '평균']]
    
    # Concatenate old and recent data
    df_item = pd.concat([df_old, df_recent])
    
    # Rename '평균' column to the item name
    df_item.rename(columns={'평균': item}, inplace=True)
    
    # Set 'Category' (Year) as index
    df_item.set_index('Category', inplace=True)
    
    dfs.append(df_item)

# Merge all dataframes along columns (axis=1)
total_df = pd.concat(dfs, axis=1)

# Sort by index (Year)
total_df.sort_index(inplace=True)

# Save the final dataframe to total_price.csv
# Saving it in the root directory for easy access/download, or could save in data_path.
# User just said "name is total_price.csv". I'll save in root.
total_df.to_csv('at_processing_data.csv')

print(total_df.head())
print(total_df.info())