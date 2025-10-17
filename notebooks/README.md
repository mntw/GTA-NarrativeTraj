# Notebooks

This folder contains three focused Jupyter notebooks used to reproduce essential figures and tables for the GTA‑NarrativeTraj project.

> **Data locations assumed by the notebooks**
>
> - Road graph: `data/graph/nodes.csv`, `data/graph/links.csv`  
> - Event log (story mode): `data/dataset/gtanarrativetraj_full_events.csv`  
> - Derived artifacts are written back to `data/dataset/` (CSV) and can be adjusted per notebook.

## 1) `01_minimal_maps.ipynb` — Minimal road‑graph maps
- **Purpose:** minimal, reusable code to draw (a) the full road graph, (b) nodes by type/flags, (c) links by class (e.g., `link_code`).  
- **Inputs:** `data/graph/nodes.csv`, `data/graph/links.csv`.  
- **Key parameters:** column mappings for coordinates (e.g., `x0,y0,x1,y1` for links and `x,y` for nodes), and the class/type column names (`type`, `is_tunnel`, `link_code`, etc.).  
- **Outputs:** on‑screen figures (can be saved by adding `plt.savefig(...)`).

## 2) `02_trip_segmentation.ipynb` — Trip segmentation
- **Purpose:** segment the event log into rides (`trip_id`) using simple heuristics that are easy to tune and reproduce.  
- **Inputs:** `data/dataset/gtanarrativetraj_full_events.csv` (columns expected: `char`, `time_rw`, `pos`, `vehicle`).  
- **Method (default):**
  1. Sort by `time_rw` within each protagonist (`char`).  
  2. Start a new trip if **(a)** time gap > `GAP_S`, **(b)** vehicle changes, or **(c)** protagonist changes.  
  3. Filter very short trips (duration < `MIN_DUR_S` or distance < `MIN_DIST_M`).  
- **Outputs:** `data/dataset/gtanarrativetraj_trips_summary.csv` with per‑trip aggregates (duration, distance, avg speed, endpoints, vehicle).

## 3) `03_text_analysis.ipynb` — Subtitle & speaker stats
- **Purpose:** compute core text statistics for the paper: total characters/tokens, non‑empty utterances, sentence counts (approx.), token statistics per utterance, and speaker distribution.  
- **Inputs:** `data/dataset/gtanarrativetraj_full_events.csv` (columns: `subtitles_text`, `speaker`).  
- **Outputs:**  
  - `data/dataset/text_stats_summary.csv` — one row per metric.  
  - `data/dataset/top_speakers.csv` — top speaker labels with counts (head 20 by default).
