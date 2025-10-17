# GTA-NarrativeTraj

A lightweight mod + pipeline for *GTA V* (Story Mode) that synchronizes trajectories with narrative signals (audio, subtitles, speakers) and logs events to CSV.  
This repository publishes a **dataset collected over ~30 hours of gameplay** and includes the sources/instructions to reproduce logging.

---

## Repository layout

```
.
├─ data/
│  ├─ dataset/
│  │  ├─ gtanarrativetraj_full_events.csv                  # full CSV log (~30 h of gameplay)
│  │  └─ gtanarrativetraj_storymode_events_by-real-date/   # daily splits + MANIFEST.csv
│  │     ├─ gtanarrativetraj_events_realdate-YYYY-MM-DD_part-PP.csv
│  │     └─ MANIFEST.csv
│  └─ graph/                                                # road graph from game path data
│     ├─ nodes.csv
│     └─ links.csv
├─ notebooks/                                               # analysis notebooks (see below)
└─ gta5-logger/                                             # mod and receiver + install guide
   ├─ README.md          # detailed setup/run instructions
   ├─ mod/               # C# (ScriptHookVDotNet) sources
   │  └─ src/
   └─ local_server/      # Python HTTP receiver → CSV writer
      ├─ server.py
      ├─ requirements.txt
      ├─ start.sh / start.bat
      └─ misc/VoiceLines.csv
```

---

## Data (`data/`)

### What’s included
- **`data/dataset/gtanarrativetraj_full_events.csv`** — the **full event-level log** collected during story-mode play (~30 hours of **in-game** time).  
- **`data/dataset/gtanarrativetraj_storymode_events_by-real-date/`** — the same log **split by real recording date**:  
  files named `gtanarrativetraj_events_realdate-YYYY-MM-DD_part-PP.csv`.  
  - `MANIFEST.csv` indexes the splits (file, date, part, record count; optionally time spans).
- **`data/graph/`** — a lane-aware road graph extracted from in-game path data:  
  `nodes.csv` (node flags/codes) and `links.csv` (width/class, lanes, transition codes).

### CSV schema (8 columns, for full log and daily splits)

| column           | brief description |
|------------------|-------------------|
| `char`           | active protagonist (Michael / Franklin / Trevor) |
| `time_ingame`    | in-game timestamp of the event |
| `time_rw`        | real-world timestamp (ISO-8601, local TZ) |
| `pos`            | world position as `x,y,z` (comma-separated string) |
| `vehicle`        | vehicle class/model if in vehicle; empty otherwise |
| `subtitles_text` | subtitle text; empty if no spoken line |
| `speaker`        | normalized speaker label/name |
| `soundfile`      | soundbank identifier/path (if available) |

**Format:** UTF-8, comma-separated, header row present.

### Daily splits (by real date)
Files `gtanarrativetraj_events_realdate-YYYY-MM-DD_part-PP.csv` contain the **same columns** as the full log, split by **real recording date** (and by `part-PP` when needed).  
`MANIFEST.csv` lists files, dates, parts, and record counts (and, when available, start/end timestamps).

---

## Notebooks (`notebooks/`)

Analysis notebooks are provided under `notebooks/`:

- `01_minimal_maps.ipynb` — minimal road‑graph plots (graph, nodes by type, links by class).  
- `02_trip_segmentation.ipynb` — trip segmentation and per‑trip aggregates; writes `gtanarrativetraj_trips_summary.csv`.  
- `03_text_analysis.ipynb` — basic text statistics and speaker distribution; writes `text_stats_summary.csv`, `top_speakers.csv`.

> Inputs: `data/dataset/gtanarrativetraj_full_events.csv`, `data/graph/nodes.csv`, `data/graph/links.csv`.  
> Outputs: CSV artifacts are written to `data/dataset/` (paths can be adjusted inside the notebooks).

---

## Mod & instructions (`gta5-logger/`)

The **`gta5-logger/`** directory contains:
- **`mod/`** — C# (ScriptHookVDotNet) sources for the GTA V logger.  
- **`local_server/`** — Python HTTP receiver that appends events to a CSV.  
- **`gta5-logger/README.md`** — the **authoritative guide** for installation and running
  (requirements, ScriptHookV/ScriptHookVDotNet setup, building the DLL, starting the receiver, CLI options).

> Default output path for the receiver:  
> `data/dataset/gtanarrativetraj_full_events.csv` (can be changed via `--out`).

---

## Notes
- Third-party binaries (ScriptHookV / ScriptHookVDotNet) are **not** redistributed here; follow the instructions in [`gta5-logger/README.md`](gta5-logger/README.md).  
- Fields `subtitles_text`, `speaker`, `soundfile` may be empty for non-spoken events.  
- Parse `pos` into three numeric columns (`x`, `y`, `z`) for downstream analysis.

---

## Acknowledgments
Co-funded by the **European Regional Development Fund (ERDF/EFRE)** and the **State of Saxony-Anhalt** under the programme *Sachsen-Anhalt WISSENSCHAFT Forschung und Innovation (EFRE) 2021–2027*, project **ReSeDiUm** (grant no. **ZS/2023/12/182669**).
