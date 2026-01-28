import os
import pandas as pd
from tqdm import tqdm

def verify_matches(xlsx_path, txt_folder, output_path):
    print(f"Loading Excel file: {xlsx_path}")
    try:
        df = pd.read_excel(xlsx_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    print(f"Loading text files from: {txt_folder}")
    if not os.path.isdir(txt_folder):
        print(f"Error: Folder '{txt_folder}' not found.")
        return

    # Map audio_filename -> list of (txt_filename, content)
    # A single audio file might be associated with multiple text files (though unlikely for this specific structure, good to be safe)
    audio_to_txt_map = {}
    
    for filename in tqdm(os.listdir(txt_folder), desc="Loading text files"):
        if filename.endswith(".txt"):
            filepath = os.path.join(txt_folder, filename)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if not lines: continue
                    
                    # First line is the audio filename
                    audio_filename = lines[0].strip()
                    
                    # Content is the rest
                    content = "".join(lines[2:]) # Assuming line 2 is blank or metadata separator based on previous analysis
                    
                    if audio_filename not in audio_to_txt_map:
                        audio_to_txt_map[audio_filename] = []
                    audio_to_txt_map[audio_filename].append({'txt_filename': filename, 'content': content})
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    print(f"Loaded {len(audio_to_txt_map)} unique audio file headers from text files.")

    # Filter for rows that have a Matched Soundfile
    rows_to_check = df[df['Matched Soundfile'].notna() & df['subtitles_text'].notna()]
    
    print(f"Found {len(rows_to_check)} rows to verify.")

    verification_results = []
    verified_count = 0
    failed_count = 0

    for index, row in tqdm(rows_to_check.iterrows(), total=len(rows_to_check), desc="Verifying matches"):
        soundfile = row['Matched Soundfile']
        subtitle = row['subtitles_text']
        
        status = "Failed"
        matched_txt = "N/A"
        
        # Check if we have text files for this audio file
        # Note: The text files have the audio filename as the first line (header)
        # We need to match 'soundfile' (from Excel) with the keys in audio_to_txt_map
        
        # Sometimes the Excel filename might have extra whitespace or extension differences
        # The map keys are exactly what was in the first line of the txt files.
        
        if soundfile in audio_to_txt_map:
            # Check if the subtitle exists in any of the associated text files
            for txt_entry in audio_to_txt_map[soundfile]:
                if subtitle in txt_entry['content']:
                    status = "Verified"
                    matched_txt = txt_entry['txt_filename']
                    break
        else:
            status = "Audio File Not Found in TXT Headers"

        if status == "Verified":
            verified_count += 1
        else:
            failed_count += 1

        verification_results.append({
            'Original Row': index + 2,
            'Subtitle': subtitle,
            'Expected Soundfile': soundfile,
            'Verification Status': status,
            'Found in TXT': matched_txt
        })

    print(f"\nVerification Complete.")
    print(f"Verified: {verified_count}")
    print(f"Failed: {failed_count}")

    # Save results
    results_df = pd.DataFrame(verification_results)
    results_df.to_excel(output_path, index=False)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    verify_matches(
        xlsx_path='received_merged_cutscene_filename.xlsx',
        txt_folder='cutscenes',
        output_path='verification_results.xlsx'
    )
