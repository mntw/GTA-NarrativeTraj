import pandas as pd

try:
    df = pd.read_excel('verification_results.xlsx')
    failed = df[df['Verification Status'] != 'Verified']
    print("--- Failed Matches ---")
    print(failed.to_string())
except Exception as e:
    print(f"Error reading results: {e}")
