import pandas as pd

try:
    df = pd.read_excel('received_merged_cutscene_filename.xlsx', nrows=5)
    print("Columns:", df.columns.tolist())
    print(df.head().to_string())
except Exception as e:
    print(f"Error reading Excel file: {e}")
