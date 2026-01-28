import pandas as pd

try:
    df = pd.read_excel('received_merged_cutscene_filename.xlsx')
    
    print("--- 'soundfile' Column Analysis ---")
    print(f"Total non-null: {df['soundfile'].count()}")
    print(f"Unique values: {df['soundfile'].nunique()}")
    print("Top 10 values:")
    print(df['soundfile'].value_counts().head(10))
    
    print("\n--- 'Matched Soundfile' Column Analysis ---")
    if 'Matched Soundfile' in df.columns:
        print(f"Total non-null: {df['Matched Soundfile'].count()}")
        print(f"Unique values: {df['Matched Soundfile'].nunique()}")
        print("Top 10 values:")
        print(df['Matched Soundfile'].value_counts().head(10))
    else:
        print("Column 'Matched Soundfile' not found.")

except Exception as e:
    print(f"Error: {e}")
