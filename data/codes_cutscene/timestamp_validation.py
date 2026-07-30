#Validation test for the number of timestamps and no of ros in excel
import argparse
import os
import pandas as pd
from pathlib import Path

def validate_data_integrity(folder_path: str, excel_path: str, audio_col: str):
    """
    Validates data integrity between audio files, their associated text files,
    and an Excel sheet.

    Args:
        folder_path: Path to the folder containing .wav and .txt files.
        excel_path: Path to the Excel file.
        audio_col: The name of the column in Excel containing audio filenames.
    """
    # 1. Setup paths and counters
    audio_dir = Path(folder_path)
    excel_file = Path(excel_path)
    report_path = "validation_report.txt"

    total_files = 0
    total_matches = 0
    total_mismatches = 0
    missing_in_excel = []
    report_lines = []

    # 2. Load Excel data
    print(f"Loading Excel file: {excel_file}")
    try:
        df = pd.read_excel(excel_file)
        if audio_col not in df.columns:
            print(f"Error: Column '{audio_col}' not found in {excel_path}. Available columns: {df.columns.tolist()}")
            return
        # Extract just the filename from the full path in the Excel column
        # and then get value counts for efficient lookup.
        # This handles both forward slashes (/) and backslashes (\).
        excel_filenames = df[audio_col].astype(str).apply(lambda x: os.path.basename(str(x)))
        excel_counts = excel_filenames.value_counts()
    except Exception as e:
        print(f"Error loading or processing Excel file: {e}")
        return

    # 3. Iterate through WAV files
    wav_files = sorted(list(audio_dir.glob("*.wav")))
    total_files = len(wav_files)
    print(f"Found {total_files} .wav files to process in '{audio_dir}'.")

    for wav_path in wav_files:
        filename = wav_path.name
        txt_path = wav_path.with_suffix('.txt')

        # 4. Get Excel row count
        excel_row_count = excel_counts.get(filename, 0)

        if excel_row_count == 0:
            missing_in_excel.append(filename)

        # 5. Get text file line count
        txt_line_count = 0
        if txt_path.exists():
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    # Count non-empty lines to be robust
                    txt_line_count = sum(1 for line in f if line.strip())
            except Exception as e:
                print(f"Warning: Could not read {txt_path}: {e}")

        # 6. Compare and determine status
        status = "Match" if excel_row_count == txt_line_count else "Mismatch"
        if status == "Match":
            total_matches += 1
        else:
            total_mismatches += 1

        report_lines.append(f"{filename:<40} | Excel Rows: {excel_row_count:<5} | TXT Lines: {txt_line_count:<5} | Status: {status}")

    # 7. Generate report file
    print(f"Generating report at: {report_path}")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=====================================\n")
        f.write("   Data Integrity Validation Report\n")
        f.write("=====================================\n\n")
        f.write(f"Total .wav files processed: {total_files}\n\n")
        f.write("--- File-by-File Breakdown ---\n")
        f.write("\n".join(report_lines))
        f.write("\n\n--- Summary ---\n")
        f.write(f"Total Matches:    {total_matches}\n")
        f.write(f"Total Mismatches: {total_mismatches}\n\n")
        if missing_in_excel:
            f.write(f"--- Files Missing from Excel ({len(missing_in_excel)}) ---\n")
            f.write("\n".join(missing_in_excel))
        else:
            f.write("--- All .wav files were found in the Excel sheet. ---\n")

    print("\n✅ Validation complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate data integrity between audio files, text files, and an Excel sheet.")
    parser.add_argument("--folder", required=True, help="Path to the folder containing .wav and .txt files.")
    parser.add_argument("--excel", required=True, help="Path to the Excel file for validation.")
    parser.add_argument("--column", default="Matched Soundfile", help="Name of the column in Excel containing audio filenames.")
    args = parser.parse_args()

    validate_data_integrity(args.folder, args.excel, args.column)
