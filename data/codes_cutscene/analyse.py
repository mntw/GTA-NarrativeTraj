import os
import argparse
import pandas as pd
from datetime import datetime
from collections import defaultdict, Counter
import string
from tqdm import tqdm

# --- CONFIGURATION: How many top hits to show in the fifth pass ---
NUM_HITS_TO_SHOW = 3

# Define punctuation set for efficient checking
PUNCTUATION_SET = set(string.punctuation)

def is_whole_phrase_match(txt_content, pos, length):
    is_start_ok = (pos == 0) or (not txt_content[pos - 1].isalnum())
    end_pos = pos + length
    is_end_ok = (end_pos == len(txt_content)) or (not txt_content[end_pos].isalnum())
    return is_start_ok and is_end_ok

def find_match_in_content(subtitle, txt_content, offset):
    search_pos = offset
    while True:
        pos = txt_content.find(subtitle, search_pos)
        if pos == -1:
            break
        if is_whole_phrase_match(txt_content, pos, len(subtitle)):
            return pos, "No"
        search_pos = pos + 1

    for i in range(offset, len(txt_content)):
        for length in range(len(subtitle) - 2, len(subtitle) + 3):
            if i + length > len(txt_content) or length <= 0:
                continue
            substring = txt_content[i : i + length]
            if compare_strings_fuzzy(subtitle, substring):
                if is_whole_phrase_match(txt_content, i, length):
                    return i, "Yes"
    return -1, "No"

def load_text_files_data(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: The text file folder '{folder_path}' was not found.")
        return None
    
    print(f"\nLoading and processing .txt files from '{folder_path}'...")
    all_text_data = []
    for filename in tqdm(os.listdir(folder_path), desc="Loading text files"):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if not lines: continue
                    
                    audio_filename = lines[0].strip()
                    non_empty_lines = [line for line in lines[2:] if line.strip()]
                    content = "".join(non_empty_lines)
                    
                    all_text_data.append({
                        'txt_filename': filename, 'audio_filename': audio_filename, 'content': content,
                        'mod_time': datetime.fromtimestamp(os.path.getmtime(filepath)),
                        'total_lines': len(lines)
                    })
            except Exception as e:
                print(f"  - Error reading file {filename}: {e}")
    
    all_text_data.sort(key=lambda x: x['mod_time'])
    print(f"  - Successfully loaded and sorted {len(all_text_data)} .txt files by modification date.")
    return all_text_data

def scan_audio_folder(audio_folder_path):
    if not audio_folder_path or not os.path.isdir(audio_folder_path):
        print("\nWarning: Audio folder path not provided or not found. Skipping audio folder check.")
        return None

    print(f"\nScanning for audio subfolders in '{audio_folder_path}'...")
    audio_subfolder_names = {item.lower() for item in os.listdir(audio_folder_path) if os.path.isdir(os.path.join(audio_folder_path, item))}
    print(f"  - Found {len(audio_subfolder_names)} unique audio subfolders.")
    return audio_subfolder_names

def group_cutscenes_into_blocks(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: The Excel file '{file_path}' was not found.")
        return None
        
    print(f"\nGrouping 'Cutscene' entries based on row order in '{os.path.basename(file_path)}'...")
    try:
        df = pd.read_excel(file_path)
        required_columns = ["subtitles_text", "speaker"]
        if not all(col in df.columns for col in required_columns): return None

        cutscene_blocks, current_block_lines, group_id_counter = [], [], 1

        for index, row in df.iterrows():
            is_cutscene_line = (pd.notna(row['speaker']) and row['speaker'].strip() == 'Cutscene' and pd.notna(row['subtitles_text']))
            is_block_breaker = (pd.notna(row['speaker']) and row['speaker'].strip() != '' and row['speaker'].strip() != 'Cutscene')

            if is_cutscene_line:
                current_subtitle = row['subtitles_text']
                is_repeat = "No"
                if current_block_lines and current_subtitle == current_block_lines[-1]['subtitle']: is_repeat = "Yes"
                current_block_lines.append({'subtitle': current_subtitle, 'original_index': index + 2, 'is_consecutive_repeat': is_repeat})
            
            if is_block_breaker and current_block_lines:
                cutscene_blocks.append({'group_id': group_id_counter, 'lines': current_block_lines})
                current_block_lines, group_id_counter = [], group_id_counter + 1

        if current_block_lines:
            cutscene_blocks.append({'group_id': group_id_counter, 'lines': current_block_lines})

        print(f"  - Identified {len(cutscene_blocks)} 'Cutscene' blocks in their original file order.")
        return cutscene_blocks

    except Exception as e:
        print(f"An error occurred while processing the Excel file: {e}")
        return None

def compare_strings_fuzzy(s1, s2):
    if s1 == s2: return True
    s1_norm = ''.join(c for c in s1 if c not in PUNCTUATION_SET)
    s2_norm = ''.join(c for c in s2 if c not in PUNCTUATION_SET)
    if s1_norm != s2_norm: return False
    
    punc_diff, p1, p2 = 0, 0, 0
    while p1 < len(s1) and p2 < len(s2):
        if s1[p1] == s2[p2]: p1, p2 = p1 + 1, p2 + 1
        elif s1[p1] in PUNCTUATION_SET: punc_diff, p1 = punc_diff + 1, p1 + 1
        elif s2[p2] in PUNCTUATION_SET: punc_diff, p2 = punc_diff + 1, p2 + 1
        else: return False
    punc_diff += sum(1 for c in s1[p1:] if c in PUNCTUATION_SET)
    punc_diff += sum(1 for c in s2[p2:] if c in PUNCTUATION_SET)
    return punc_diff <= 2

def find_block_matches(block_lines, txt_content, start_offset):
    search_offset = start_offset
    found_matches_details = []
    unfound_lines_info = []
    
    previous_subtitle = None

    for line_info in block_lines:
        current_subtitle = line_info['subtitle']
        
        if current_subtitle == previous_subtitle:
            match_detail = {**line_info, 'punc_diff': 'No', 'gap': 'No'}
            found_matches_details.append(match_detail)
            continue

        pos, punc_diff = find_match_in_content(current_subtitle, txt_content, search_offset)
        
        if pos != -1:
            gap = "Yes" if pos > search_offset else "No"
            match_detail = {**line_info, 'punc_diff': punc_diff, 'gap': gap}
            found_matches_details.append(match_detail)

            search_offset = pos + len(current_subtitle)
            previous_subtitle = current_subtitle
        else:
            unfound_lines_info.append(line_info)

    return found_matches_details, unfound_lines_info, search_offset

def perform_first_pass_matching(cutscene_blocks, text_files):
    print("\nPerforming first pass match analysis (whole phrase)...")
    matches_raw, unmatched_raw, group_statuses = [], [], {}
    
    txt_file_states = [{'file_info': tf, 'search_offset': 0} for tf in text_files]

    for block in tqdm(cutscene_blocks, desc="Analyzing cutscene blocks"):
        best_match_count, best_results = -1, None
        
        for state in txt_file_states:
            found_matches, unfound_lines, end_offset = find_block_matches(
                block['lines'], state['file_info']['content'], state['search_offset']
            )
            
            if len(found_matches) > best_match_count:
                best_match_count = len(found_matches)
                best_results = {
                    'state': state, 'found_matches': found_matches,
                    'unfound_lines': unfound_lines, 'end_offset': end_offset
                }
        
        if best_match_count > 0:
            status = 'Complete' if not best_results['unfound_lines'] else 'Partial'
            group_statuses[block['group_id']] = status
            
            best_results['state']['search_offset'] = best_results['end_offset']

            for match_detail in best_results['found_matches']:
                matches_raw.append({
                    'group_id': block['group_id'], 
                    'txt_file_info': best_results['state']['file_info'], 
                    **match_detail
                })
            
            for line_info in best_results['unfound_lines']:
                unmatched_raw.append({'group_id': block['group_id'], **line_info})
        else:
            group_statuses[block['group_id']] = 'Unmatched'
            for line_info in block['lines']:
                unmatched_raw.append({'group_id': block['group_id'], **line_info})

    unmatched_txt_files = [state['file_info'] for state in txt_file_states if state['search_offset'] == 0]
    
    print("  - First pass complete.")
    return matches_raw, unmatched_raw, unmatched_txt_files, group_statuses

def perform_second_pass_analysis(unmatched_raw, group_statuses, matches_raw, all_cutscene_blocks):
    print("\nPerforming second pass analysis on PARTIAL matches...")
    second_pass_results = {}
    group_id_to_txt_file = {m['group_id']: m['txt_file_info'] for m in matches_raw if m['txt_file_info']}
    group_id_to_full_block = {b['group_id']: b for b in all_cutscene_blocks}
    
    partial_unmatched = [um for um in unmatched_raw if group_statuses.get(um['group_id']) == 'Partial']
    for um in tqdm(partial_unmatched, desc="Analyzing partial matches"):
        group_id = um['group_id']
        txt_file = group_id_to_txt_file.get(group_id)
        full_block = group_id_to_full_block.get(group_id)
        if txt_file and full_block:
            full_block_subtitles = [line['subtitle'] for line in full_block['lines']]
            match_score = sum(1 for sub in full_block_subtitles if sub in txt_file['content'])
            percentage = (match_score / len(full_block_subtitles)) * 100
            key = (group_id, um['original_index'])
            second_pass_results[key] = {
                'Best Match TXT': txt_file['txt_filename'], 'Best Match TXT Content': txt_file['content'],
                'Group Match Percentage': f"{percentage:.2f}%"
            }
    print("  - Second pass complete.")
    return second_pass_results

def perform_third_pass_analysis(unmatched_raw, group_statuses, all_text_files, all_cutscene_blocks):
    print("\nPerforming third pass analysis on UNMATCHED groups...")
    third_pass_results = {}
    group_id_to_full_block = {b['group_id']: b for b in all_cutscene_blocks}

    unmatched_groups_to_check = {um['group_id'] for um in unmatched_raw if group_statuses.get(um['group_id']) == 'Unmatched'}

    for group_id in tqdm(unmatched_groups_to_check, desc="Analyzing unmatched groups"):
        full_block = group_id_to_full_block.get(group_id)
        if not full_block: continue
        full_block_subtitles = [line['subtitle'] for line in full_block['lines']]
        
        best_txt_file, best_score = None, -1
        for txt_file in all_text_files:
            score = sum(1 for sub in full_block_subtitles if sub in txt_file['content'])
            if score > best_score:
                best_score, best_txt_file = score, txt_file
        
        if best_txt_file:
            percentage = (best_score / len(full_block_subtitles)) * 100
            for line in full_block['lines']:
                key = (group_id, line['original_index'])
                third_pass_results[key] = {
                    'Best Match TXT': best_txt_file['txt_filename'], 'Best Match TXT Content': best_txt_file['content'],
                    'Best Match Audio Filename': best_txt_file['audio_filename'],
                    'Group Match Percentage': f"{percentage:.2f}%"
                }
    print("  - Third pass complete.")
    return third_pass_results

def perform_fourth_pass_analysis(matches_raw, group_statuses, all_text_files, all_cutscene_blocks):
    print("\nPerforming fourth pass analysis to verify PARTIAL matches...")
    fourth_pass_results = {}
    group_id_to_full_block = {b['group_id']: b for b in all_cutscene_blocks}

    partial_groups_to_check = {m['group_id'] for m in matches_raw if group_statuses.get(m['group_id']) == 'Partial'}
    
    original_match_info = defaultdict(lambda: {'count': 0, 'file': None})
    for m in matches_raw:
        if m['group_id'] in partial_groups_to_check:
            original_match_info[m['group_id']]['count'] += 1
            original_match_info[m['group_id']]['file'] = m['txt_file_info']['txt_filename']

    for group_id in tqdm(partial_groups_to_check, desc="Verifying partial matches"):
        full_block = group_id_to_full_block.get(group_id)
        if not full_block: continue
        full_block_subtitles = [line['subtitle'] for line in full_block['lines']]
        
        best_txt_file, best_score = None, -1
        for txt_file in all_text_files:
            score = sum(1 for sub in full_block_subtitles if sub in txt_file['content'])
            if score > best_score:
                best_score, best_txt_file = score, txt_file
        
        original_count = original_match_info[group_id]['count']
        if best_score > original_count:
            percentage = (best_score / len(full_block_subtitles)) * 100
            for line in full_block['lines']:
                key = (group_id, line['original_index'])
                fourth_pass_results[key] = {
                    'Better Match Found?': 'Yes',
                    'Better Match TXT': best_txt_file['txt_filename'],
                    'Better Match Score': f"{percentage:.2f}%"
                }
    print("  - Fourth pass complete.")
    return fourth_pass_results

def get_word_counts(text):
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.lower().translate(translator)
    return Counter(cleaned_text.split())

def perform_fifth_pass_analysis(unmatched_raw, all_text_files):
    print("\nPerforming fifth pass (word-by-word, multiple hits) analysis on all unmatched subtitles...")
    fifth_pass_results = {}

    print("  - Pre-caching word counts from all TXT files...")
    txt_word_counts_cache = {
        tf['txt_filename']: get_word_counts(tf['content']) 
        for tf in tqdm(all_text_files, desc="Caching TXT files")
    }

    for um in tqdm(unmatched_raw, desc="Analyzing unmatched subtitles (word-by-word)"):
        subtitle_text = um['subtitle']
        subtitle_word_counts = get_word_counts(subtitle_text)
        total_words_in_subtitle = sum(subtitle_word_counts.values())
        if total_words_in_subtitle == 0:
            continue

        all_file_scores = []
        for txt_filename, txt_word_counts in txt_word_counts_cache.items():
            total_words_matched = 0
            for word, required_count in subtitle_word_counts.items():
                found_count = txt_word_counts.get(word, 0)
                total_words_matched += min(required_count, found_count)
            
            score = (total_words_matched / total_words_in_subtitle) * 100
            if score > 0:
                all_file_scores.append({'filename': txt_filename, 'score': score})

        all_file_scores.sort(key=lambda x: x['score'], reverse=True)
        top_hits = all_file_scores[:NUM_HITS_TO_SHOW]

        if top_hits:
            key = (um['group_id'], um['original_index'])
            fifth_pass_results[key] = top_hits

    print("  - Fifth pass complete.")
    return fifth_pass_results

def save_report_to_excel(report_data, output_path):
    print(f"\nSaving analysis report to '{output_path}'...")
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            pd.DataFrame(report_data['summary']).to_excel(writer, sheet_name='Summary', index=False)
            
            matches_df = pd.DataFrame(report_data['matches'])
            unmatched_df = pd.DataFrame(report_data['unmatched_subtitles'])
            
            matches_df.to_excel(writer, sheet_name='Successful Matches', index=False)
            unmatched_df.to_excel(writer, sheet_name='Unmatched Excel Subtitles', index=False)
            
            unmatched_txt_df = pd.DataFrame(report_data['unmatched_txt_files'])
            if not unmatched_txt_df.empty:
                cols = ['txt_filename', 'audio_filename', 'Audio Folder Found', 'total_lines', 'mod_time']
                unmatched_txt_df = unmatched_txt_df.reindex(columns=[c for c in cols if c in unmatched_txt_df.columns])
            unmatched_txt_df.to_excel(writer, sheet_name='Unmatched TXT Files', index=False)
        
        print("  - Analysis report saved successfully.")
    except Exception as e:
        print(f"  - Error: Could not save the analysis report. {e}")

def update_excel_with_matches(original_xlsx_path, updated_xlsx_path, all_row_updates):
    print(f"\nUpdating Excel file with full context...")
    try:
        df = pd.read_excel(original_xlsx_path)

        update_cols = {
            'soundfile': 'Matched Soundfile', 'group_id': 'Cutscene Group ID',
            'txt_filename': 'Matched TXT Filename', 'txt_content': 'Matched TXT Content',
            'group_status': 'Group Match Status', 'repeat': 'Consecutive Repeat',
            'punc_diff': 'Punctuation Difference', 'gap': 'Gap In TXT',
            'percentage': 'Group Match Percentage'
        }

        insert_pos = df.columns.get_loc('subtitles_text') + 1 if 'subtitles_text' in df.columns else 2
        for col_name in reversed(list(update_cols.values())):
            if col_name not in df.columns:
                df.insert(insert_pos, col_name, pd.NA)

        for row_num, data in all_row_updates.items():
            df_index = row_num - 2
            if 0 <= df_index < len(df):
                for key, value in data.items():
                    df.loc[df_index, update_cols[key]] = value

        df.to_excel(updated_xlsx_path, index=False)
        print(f"  - Successfully created updated Excel file at '{updated_xlsx_path}'")

    except Exception as e:
        print(f"  - Error: Could not create or update the Excel file. {e}")
        
def main():
    parser = argparse.ArgumentParser(description="A comprehensive tool to analyze, match, and validate subtitle data.")
    parser.add_argument("--txt-folder", required=True, help="Path to the folder with .txt files.")
    parser.add_argument("--xlsx-file", required=True, help="Path to the .xlsx file for analysis.")
    parser.add_argument("--subtract", type=int, default=364, help="A constant number to subtract from the .txt line count.")
    parser.add_argument("--output", type=str, default="full_analysis_report.xlsx", help="Path for the output analysis report file.")
    parser.add_argument("--audio-folder", type=str, help="[Optional] Path to the main folder with audio subfolders.")
    parser.add_argument("--update-xlsx", type=str, help="[Optional] Path to save a new Excel file with matched data.")
    parser.add_argument("--run-second-pass", action='store_true', help="[Optional] Run the second pass analysis on partially matched groups.")
    parser.add_argument("--run-third-pass", action='store_true', help="[Optional] Run the third pass analysis on completely unmatched groups.")
    parser.add_argument("--run-fourth-pass", action='store_true', help="[Optional] Run a fourth pass to verify partial matches against all files.")
    parser.add_argument("--run-fifth-pass", action='store_true', help="[Optional] Run a fifth pass (word-by-word) on all unmatched subtitles.")
    args = parser.parse_args()

    text_files = load_text_files_data(args.txt_folder)
    cutscene_blocks = group_cutscenes_into_blocks(args.xlsx_file)
    audio_subfolder_set = scan_audio_folder(args.audio_folder)
    if text_files is None or cutscene_blocks is None: return

    matches_raw, unmatched_raw, unmatched_txt_files, group_statuses = perform_first_pass_matching(cutscene_blocks, text_files)
    
    second_pass_results, third_pass_results, fourth_pass_results, fifth_pass_results = {}, {}, {}, {}
    if args.run_second_pass:
        second_pass_results = perform_second_pass_analysis(unmatched_raw, group_statuses, matches_raw, cutscene_blocks)
    else:
        print("\nSkipping second pass analysis (use --run-second-pass to enable).")

    if args.run_third_pass:
        third_pass_results = perform_third_pass_analysis(unmatched_raw, group_statuses, text_files, cutscene_blocks)
    else:
        print("Skipping third pass analysis (use --run-third-pass to enable).")

    if args.run_fourth_pass:
        fourth_pass_results = perform_fourth_pass_analysis(matches_raw, group_statuses, text_files, cutscene_blocks)
    else:
        print("Skipping fourth pass analysis (use --run-fourth-pass to enable).")
    
    if args.run_fifth_pass:
        fifth_pass_results = perform_fifth_pass_analysis(unmatched_raw, text_files)
    else:
        print("Skipping fifth pass analysis (use --run-fifth-pass to enable).")

    final_matches, final_unmatched = [], []
    for match in matches_raw:
        txt_info = match['txt_file_info']
        final_matches.append({
            'Cutscene Group ID': match['group_id'], 'Group Match Status': group_statuses.get(match['group_id']),
            'Gap In TXT': match.get('gap', 'N/A'), 'Consecutive Repeat': match['is_consecutive_repeat'],
            'Punctuation Difference': match['punc_diff'], 
            'TXT Filename': txt_info['txt_filename'] if txt_info else 'N/A',
            'Audio Filename': txt_info['audio_filename'] if txt_info else 'N/A', 
            'Full TXT Content': txt_info['content'] if txt_info else '',
            'Matched Excel Subtitle': match['subtitle'], 'Original Excel Row': match['original_index']
        })

    for um in unmatched_raw:
        analysis_info = second_pass_results.get((um['group_id'], um['original_index'])) or third_pass_results.get((um['group_id'], um['original_index']), {})
        fourth_pass_info = fourth_pass_results.get((um['group_id'], um['original_index']), {})
        fifth_pass_info = fifth_pass_results.get((um['group_id'], um['original_index']), [])
        
        # --- THE FIX IS HERE ---
        unmatched_row = {
            'Cutscene Group ID': um['group_id'], 'Group Match Status': group_statuses.get(um['group_id']), 
            'Consecutive Repeat': um['is_consecutive_repeat'], 'Unmatched Subtitle': um['subtitle'], 
            'Original Excel Row': um['original_index'], 
            'Best Match TXT': analysis_info.get('Best Match TXT', 'N/A'), 
            'Best Match TXT Content': analysis_info.get('Best Match TXT Content', ''), # Added this line
            'Group Match Percentage': analysis_info.get('Group Match Percentage', '0.00%'), 
            'Best Match Audio Filename': analysis_info.get('Best Match Audio Filename'),
            'Better Match Found?': fourth_pass_info.get('Better Match Found?', 'No'),
            'Better Match TXT': fourth_pass_info.get('Better Match TXT', 'N/A'),
            'Better Match Score': fourth_pass_info.get('Better Match Score', 'N/A'),
        }

        for i in range(NUM_HITS_TO_SHOW):
            if i < len(fifth_pass_info):
                hit = fifth_pass_info[i]
                unmatched_row[f'Word Match {i+1} TXT'] = hit['filename']
                unmatched_row[f'Word Match {i+1} Score'] = f"{hit['score']:.2f}%"
            else:
                unmatched_row[f'Word Match {i+1} TXT'] = 'N/A'
                unmatched_row[f'Word Match {i+1} Score'] = 'N/A'

        final_unmatched.append(unmatched_row)

    if audio_subfolder_set:
        for item in final_matches: 
            if item['Audio Filename'] != 'N/A':
                item['Audio Folder Found'] = 'Yes' if os.path.splitext(item['Audio Filename'])[0].lower() in audio_subfolder_set else 'No'
        for item in unmatched_txt_files: item['Audio Folder Found'] = 'Yes' if os.path.splitext(item['audio_filename'])[0].lower() in audio_subfolder_set else 'No'

    final_txt_line_count = (sum(tf['total_lines'] for tf in text_files) - len(text_files)) - args.subtract
    complete, partial, unmatched = [sum(1 for s in group_statuses.values() if s == val) for val in ['Complete', 'Partial', 'Unmatched']]
    summary_metrics = ['FINAL Adjusted .txt Line Count', 'Cutscene Groups: Total', 'Cutscene Groups: Complete Match', 'Cutscene Groups: Partial Match', 'Cutscene Groups: No Match', '"Cutscene" rows from Excel matched', '"Cutscene" rows from Excel NOT matched']
    summary_values = [final_txt_line_count, len(group_statuses), complete, partial, unmatched, len(final_matches), len(final_unmatched)]
    if audio_subfolder_set:
        found_count = sum(1 for name in {tf['audio_filename'] for tf in text_files} if os.path.splitext(name)[0].lower() in audio_subfolder_set)
        summary_metrics.extend(['Audio Folders: Total Referenced', 'Audio Folders: Found', 'Audio Folders: Missing'])
        summary_values.extend([len({tf['audio_filename'] for tf in text_files}), found_count, len({tf['audio_filename'] for tf in text_files}) - found_count])
    report_data = {'summary': {'Metric': summary_metrics, 'Value': summary_values}, 'matches': final_matches, 'unmatched_subtitles': final_unmatched, 'unmatched_txt_files': unmatched_txt_files}
    save_report_to_excel(report_data, args.output)
    
    if args.update_xlsx:
        all_row_updates = {}
        for block in cutscene_blocks:
            for line in block['lines']:
                all_row_updates[line['original_index']] = {'group_id': block['group_id']}
        
        for m in final_matches:
            all_row_updates[m['Original Excel Row']].update({
                'soundfile': m['Audio Filename'], 'txt_filename': m['TXT Filename'],
                'txt_content': m['Full TXT Content'], 'group_status': m['Group Match Status'],
                'repeat': m['Consecutive Repeat'], 'punc_diff': m['Punctuation Difference'],
                'gap': m['Gap In TXT']
            })
        
        for um in final_unmatched:
            all_row_updates[um['Original Excel Row']].update({
                'group_status': um['Group Match Status'], 'repeat': um['Consecutive Repeat'],
                'percentage': um['Group Match Percentage']
            })
            if um['Group Match Percentage'] == '100.00%':
                all_row_updates[um['Original Excel Row']].update({
                    'soundfile': um['Best Match Audio Filename'],
                    'txt_filename': um['Best Match TXT'],
                    'txt_content': um['Best Match TXT Content']
                })
        
        update_excel_with_matches(args.xlsx_file, args.update_xlsx, all_row_updates)

    print("\n\n================================ SUMMARY ================================")
    for i in range(len(report_data['summary']['Metric'])): print(f"{report_data['summary']['Metric'][i]}: {report_data['summary']['Value'][i]}")
    print(f"\nDetailed analysis report saved to: {args.output}")
    if args.update_xlsx: print(f"Updated Excel data with full context saved to: {args.update_xlsx}")
    print("======================================================================")

if __name__ == "__main__":
    main()