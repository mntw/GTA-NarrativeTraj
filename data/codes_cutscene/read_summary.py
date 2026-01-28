import pandas as pd

try:
    df = pd.read_excel('all_pass_pc_5th.xlsx', sheet_name='Sheet1', nrows=5)
    print(df.to_string())
    print("\nColumns:", df.columns.tolist())
except Exception as e:
    print(f"Error reading Excel file: {e}")
