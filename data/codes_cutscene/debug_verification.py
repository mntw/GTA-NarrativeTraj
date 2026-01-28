import pandas as pd
import os

print("--- First 5 rows of verification results ---")
try:
    df = pd.read_excel('verification_results.xlsx', nrows=5)
    print(df.to_string())
except Exception as e:
    print(f"Error reading results: {e}")

print("\n--- Header of 'cutscenes/ah_1_mcs_1.cut.txt' ---")
try:
    with open('cutscenes/ah_1_mcs_1.cut.txt', 'r') as f:
        print(f.read(100)) # Read first 100 chars
except Exception as e:
    print(f"Error reading file: {e}")

print("\n--- Header of another file ---")
try:
    # List one more file to check
    files = [f for f in os.listdir('cutscenes') if f.endswith('.txt')]
    if len(files) > 1:
        with open(os.path.join('cutscenes', files[1]), 'r') as f:
            print(f"File: {files[1]}")
            print(f.read(100))
except Exception as e:
    print(f"Error reading file: {e}")
