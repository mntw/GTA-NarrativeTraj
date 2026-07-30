import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1" 

import pandas as pd
import torch
import soundfile as sf
import scipy.signal as signal
from speechbrain.inference.speaker import EncoderClassifier
from pathlib import Path
from tqdm import tqdm

# ==============================================================================
# Configuration
# ==============================================================================

ENROLLMENT_EXCEL_PATH = r"C:/Users/student/Desktop/dev/aurora/datasets/gta/gtanarrativetraj_full_events_cutscene_soundfile_missingfiles_verified_extended_verified_100pct.xlsx"
ENROLLMENT_AUDIO_FOLDER = r"C:/Users/student/Desktop/dev/aurora/datasets/gta/icaiit/Audio+Text/audio"
TARGET_EXCEL_PATH = r"C:/Users/student/Desktop/dev/aurora/datasets/gta/gtanarrativetraj_full_events_cutscene_soundfile_missingfiles_verified.xlsx"
TARGET_AUDIO_FOLDER = r"C:/Users/student/Desktop/dev/aurora/datasets/gta/audio/cutscene_prologue_sorted/trimmed_annotated"
LEGEND_FILE_PATH = r"C:/Users/student/Desktop/dev/aurora/datasets/gta/audio/cutscene_prologue_sorted/trimmed_annotated/Legends.txt"
OUTPUT_EXCEL_PATH = "speaker_classification_FINAL.xlsx"
REMAINING_OUTPUT_EXCEL_PATH = "speaker_classification_remaining_enroll.xlsx"

# DURATION CONSTRAINTS
ENROLL_MIN_DURATION = 5.0  # Must be 1s+ to count for enrollment
ENROLL_MAX_CUMULATIVE_DURATION = 100 # Maximum total audio duration per speaker for enrollment
INFER_MIN_DURATION = 2   # Must be 0.5s+ to be classified
SIMILARITY_THRESHOLD = 0.5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ==============================================================================

def get_speaker_embedding(classifier, audio_path: Path, start_sec: float, end_sec: float, min_dur: float):
    try:
        # Load audio using soundfile (Bypasses torchaudio metadata issues)
        data, sr = sf.read(str(audio_path), dtype='float32')
        
        # Calculate start/end frames
        start_frame = int(start_sec * sr)
        end_frame = int(end_sec * sr)
        
        # Check duration
        duration = (end_frame - start_frame) / sr
        if duration < min_dur: return None
        
        # Handle stereo -> mono
        if len(data.shape) > 1: data = data[:, 0]
        
        # Safety bounds
        if end_frame > len(data): end_frame = len(data)
        if end_frame <= start_frame: return None
        
        # Extract segment
        segment = data[start_frame:end_frame]
        
        # Resample using scipy (Bypasses torchaudio.transforms)
        target_sr = 16000 
        if sr != target_sr:
            num_samples = int(len(segment) * target_sr / sr)
            segment = signal.resample(segment, num_samples)
            
        segment_tensor = torch.tensor(segment).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            emb = classifier.encode_batch(segment_tensor)
            return torch.nn.functional.normalize(emb.squeeze(), dim=-1)
    except Exception:
        return None

def main():
    print(f"✅ Using device: {DEVICE}")
    model_save_dir = os.path.abspath('pretrained_models')
    
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb", 
        savedir=model_save_dir, 
        run_opts={"device": DEVICE}
    )

    # --- 1. Enrollment Phase ---
    print("\n--- Starting Enrollment Phase ---")
    enrolled_speakers = {}
    enroll_df = pd.read_excel(ENROLLMENT_EXCEL_PATH)
    
    # NORMALIZATION: lowercase and strip spaces
    enroll_df['speaker'] = enroll_df['speaker'].astype(str).str.lower().str.strip()
    enroll_df = enroll_df[enroll_df['speaker'].notna() & (enroll_df['speaker'] != 'nan') & (enroll_df['speaker'] != '')]
    enroll_df['exact_audio_used'] = enroll_df['exact_audio_used'].astype(str).replace('nan', '')
    
    all_enroll_files = {f.name: f for f in Path(ENROLLMENT_AUDIO_FOLDER).rglob("*.wav")}
    
    used_indices = set()
    enroll_log_lines = []
    
    for speaker_name, group in enroll_df.groupby('speaker'):
        valid_clips = []
        for idx, row in group.iterrows():
            fname = os.path.basename(row['exact_audio_used']).strip()
            f = all_enroll_files.get(fname)
            if f and f.exists():
                info = sf.info(str(f))
                if info.duration >= ENROLL_MIN_DURATION:
                    valid_clips.append((idx, row, info.duration, f))
        
        # Sort by duration descending (choose top ones)
        valid_clips.sort(key=lambda x: x[2], reverse=True)
        
        selected_clips = []
        cumulative_time = 0.0
        
        for clip in valid_clips:
            if cumulative_time >= ENROLL_MAX_CUMULATIVE_DURATION:
                break
            selected_clips.append(clip)
            cumulative_time += clip[2]
            
        embs = []
        used_files = []
        for clip in selected_clips:
            idx, row, dur, f = clip
            e = get_speaker_embedding(classifier, f, 0, dur, min_dur=ENROLL_MIN_DURATION)
            if e is not None:
                embs.append(e)
                used_files.append(f.name)
                used_indices.add(idx)
        
        if embs:
            enrolled_speakers[speaker_name] = torch.stack(embs).mean(dim=0)
            log_str = f"  ✅ Enrolled {speaker_name}: used {len(embs)} clips, total time: {cumulative_time:.2f}s\n     Files: {', '.join(used_files)}"
            print(log_str)
            enroll_log_lines.append(log_str)
            
    # Save log to text file
    with open("enrollment_log.txt", "w", encoding="utf-8") as lf:
        lf.write("\n".join(enroll_log_lines))
    
    print(f"\n✅ Successfully enrolled {len(enrolled_speakers)} unique normalized speakers.")

    # --- 1.5 Evaluate Remaining Enrollment Files ---
    print("\n--- Evaluating Remaining Enrollment Files ---")
    remaining_enroll_df = enroll_df.drop(list(used_indices)).copy()
    remaining_enroll_df['sp_cl'] = "Pending"
    remaining_enroll_df['Match_Status'] = "Pending"
    
    for idx, row in tqdm(remaining_enroll_df.iterrows(), total=len(remaining_enroll_df), desc="Eval Remaining"):
        fname = os.path.basename(row['exact_audio_used']).strip()
        f = all_enroll_files.get(fname)
        if not f or not f.exists():
            remaining_enroll_df.at[idx, 'sp_cl'] = "Err: Missing File"
            continue
            
        try:
            info = sf.info(str(f))
            emb = get_speaker_embedding(classifier, f, 0, info.duration, min_dur=INFER_MIN_DURATION)
            
            if emb is None:
                remaining_enroll_df.at[idx, 'sp_cl'] = f"Skipped (<{INFER_MIN_DURATION}s)"
                remaining_enroll_df.at[idx, 'Match_Status'] = "Skipped"
                continue
                
            best_spk, high_sim = "Unknown", -1.0
            for name, spk_emb in enrolled_speakers.items():
                sim = torch.nn.functional.cosine_similarity(emb.unsqueeze(0), spk_emb.unsqueeze(0)).item()
                if sim > high_sim: high_sim, best_spk = sim, name
                
            if high_sim >= SIMILARITY_THRESHOLD:
                remaining_enroll_df.at[idx, 'sp_cl'] = f"{best_spk.title()} ({high_sim:.2f})"
                target_name = str(row['speaker']).strip().lower()
                remaining_enroll_df.at[idx, 'Match_Status'] = "Match" if best_spk == target_name else "Mismatch"
            else:
                remaining_enroll_df.at[idx, 'sp_cl'] = f"Low Conf ({best_spk.title()} {high_sim:.2f})"
                remaining_enroll_df.at[idx, 'Match_Status'] = "Low Confidence"
        except Exception:
            remaining_enroll_df.at[idx, 'sp_cl'] = "Err: Processing"
            
    completed_rem_df = remaining_enroll_df[remaining_enroll_df['Match_Status'].isin(['Match', 'Mismatch'])]
    if not completed_rem_df.empty:
        rem_accuracy = (completed_rem_df['Match_Status'] == 'Match').mean()
        print(f"\n✅ Accuracy on Remaining Enrollment Files: {rem_accuracy:.2%}")
        
    remaining_enroll_df.to_excel(REMAINING_OUTPUT_EXCEL_PATH, index=False)
    print(f"✅ Saved remaining enrollment eval to {REMAINING_OUTPUT_EXCEL_PATH}")

    # --- 2. Inference Phase ---
    print("\n--- Starting Inference Phase ---")
    legend_map = {}
    try:
        with open(LEGEND_FILE_PATH, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if '-' in line:
                    parts = line.split('-', 1)
                    legend_map[parts[0].strip().lower()] = parts[1].strip()
    except: pass

    target_df = pd.read_excel(TARGET_EXCEL_PATH)
    target_df['Matched Soundfile'] = target_df['Matched Soundfile'].astype(str).replace('nan', '')
    target_df[['Manual_Name', 'sp_cl', 'Match_Status']] = "Pending"

    for idx, row in tqdm(target_df.iterrows(), total=len(target_df), desc="Processing"):
        fname = os.path.basename(str(row['Matched Soundfile']))
        wav = Path(TARGET_AUDIO_FOLDER) / fname
        txt = wav.with_suffix('.txt')
        
        if not wav.exists() or not txt.exists():
            target_df.at[idx, 'Manual_Name'] = "Err: Missing File"
            continue

        try:
            with open(txt, 'r', encoding='utf-8-sig') as f:
                lines = [l.split() for l in f if l.strip()]
            
            group = target_df[target_df['Matched Soundfile'].apply(os.path.basename) == fname]
            sub_idx = group.index.get_loc(idx)
            if sub_idx >= len(lines): continue
            
            start, end, acr = float(lines[sub_idx][0]), float(lines[sub_idx][1]), lines[sub_idx][2]
            target_df.at[idx, 'Manual_Name'] = legend_map.get(acr.lower(), "Unknown").title()
            
            # Using specific Inference duration constraint
            emb = get_speaker_embedding(classifier, wav, start, end, min_dur=INFER_MIN_DURATION)
            
            if emb is None:
                target_df.at[idx, 'sp_cl'] = f"Skipped (<{INFER_MIN_DURATION}s)"
                target_df.at[idx, 'Match_Status'] = "Skipped"
                continue
            
            best_spk, high_sim = "Unknown", -1.0
            for name, spk_emb in enrolled_speakers.items():
                sim = torch.nn.functional.cosine_similarity(emb.unsqueeze(0), spk_emb.unsqueeze(0)).item()
                if sim > high_sim: high_sim, best_spk = sim, name
            
            if high_sim >= SIMILARITY_THRESHOLD:
                target_df.at[idx, 'sp_cl'] = f"{best_spk.title()} ({high_sim:.2f})"
                target_df.at[idx, 'Match_Status'] = "Match" if best_spk == target_df.at[idx, 'Manual_Name'].lower() else "Mismatch"
            else:
                target_df.at[idx, 'sp_cl'] = f"Low Conf ({best_spk.title()} {high_sim:.2f})"
                target_df.at[idx, 'Match_Status'] = "Low Confidence"
                
        except Exception:
            target_df.at[idx, 'Manual_Name'] = "Err: Processing"

    # Accuracy Calculation
    completed_df = target_df[target_df['Match_Status'].isin(['Match', 'Mismatch'])]
    if not completed_df.empty:
        accuracy = (completed_df['Match_Status'] == 'Match').mean()
        print(f"\n✅ Accuracy on Valid Matches: {accuracy:.2%}")
    
    target_df.to_excel(OUTPUT_EXCEL_PATH, index=False)
    print(f"\n✅ Done! Saved to {OUTPUT_EXCEL_PATH}")

if __name__ == "__main__":
    main()