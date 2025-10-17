# World Logging

A lightweight setup for logging in‑game data from **GTA V (single‑player)** to CSV. The repository contains two components that work together:

- **Game Mod** (C#, ScriptHookVDotNet) — emits structured log lines from the running game.
- **Local Server** (Python, `aiohttp`) — receives lines over HTTP and appends them to CSV.

> **Note:** These tools are intended for single‑player only. Do not use in GTA Online.

---

## Repository layout

```
.
├── local_server/                # logging receiver (Python)
│   ├── requirements.txt
│   ├── server.py
│   ├── start.bat
│   └── start.sh
└── mod/                         # game mod (C# / ScriptHookVDotNet)
    ├── src/                     # mod source
    ├── prerequisites/           # third‑party binaries (see below)
    └── bin/                     # build outputs
        └── scripts/
```

---

## Prerequisites (ScriptHookV & ScriptHookVDotNet)

The mod depends on two external components that must be obtained from their official channels and placed into `mod/prerequisites/`.

### 1) ScriptHookVDotNet (SHVDN)

- **Official channel (releases):** <https://github.com/scripthookvdotnet/scripthookvdotnet/releases>
- **Copy these files** from the release ZIP into `mod/prerequisites/`:
  - `ScriptHookVDotNet.asi`
  - `ScriptHookVDotNet2.dll`
  - `ScriptHookVDotNet3.dll`
  - *(optional, recommended)* `LICENSE.txt`, `README.txt`, `ScriptHookVDotNet2.xml`, `ScriptHookVDotNet3.xml`
- `ScriptHookVDotNet.ini` is already present in `mod/prerequisites/` (tweak as needed).

### 2) ScriptHookV (Alexander Blade)

- **Official site:** <http://www.dev-c.com/gtav/>
- Download the ZIP and **copy these files** into `mod/prerequisites/`:
  - `ScriptHookV.dll`
  - `dinput8.dll`
  - `xinput1_4.dll`

> In an actual GTA V installation, `dinput8.dll` and `ScriptHookV.dll` live in the game root. Here they are staged under `mod/prerequisites/` so build/post‑copy steps can use them.

**Resulting `prerequisites/` (example):**
```
mod/prerequisites/
├─ ScriptHookVDotNet.asi
├─ ScriptHookVDotNet2.dll
├─ ScriptHookVDotNet3.dll
├─ ScriptHookVDotNet.ini
├─ ScriptHookV.dll
├─ dinput8.dll
├─ xinput1_4.dll
├─ LICENSE.txt      # from SHVDN release (optional, recommended)
└─ README.txt       # from SHVDN release (optional)
```

---

## Local server

### Requirements
- Python **3.8+**

Install dependencies:
```bash
pip install -r local_server/requirements.txt
```

### Running
Start the receiver either directly or via helper scripts.

- **Direct (CLI):**
  ```bash
  cd local_server
  python server.py --host 0.0.0.0 --port 8080
  ```

- **Windows helper:**
  ```bash
  local_server\start.bat
  ```

- **Linux/macOS helper:**
  ```bash
  ./local_server/start.sh
  ```

#### CLI arguments
- `--host` (or `-H`): address to bind (e.g., `127.0.0.1`, `0.0.0.0`)
- `--port` (or `-P`): port number (default `8080`)

> By default the server writes all received lines to a CSV file named after the **server start timestamp**, e.g., `received_YYYYMMDD_HHMMSS_mmmmmm.csv`. If your version of `server.py` supports an `--out` argument, you can point it to a specific destination CSV instead.

---

## Mod (C# / SHVDN)

### Preparation
- Ensure **Microsoft .NET Framework 4.8** and **Microsoft Visual C++ Redistributable 2019 (x64)** are installed.
- Copy files from `mod/prerequisites/` into the proper locations for your GTA V install (for development, keeping them in `prerequisites/` is sufficient when post‑build steps copy them automatically).
- Launch the game once so ScriptHookVDotNet initializes.
- *(optional)* Configure a hotkey to reload scripts in `ScriptHookVDotNet.ini` via `ReloadKeyBinding`.

### Installation
- Copy the contents of `mod/bin/scripts/` (or your build output) into the game’s `scripts/` folder.

### Running
1. Start the **local server** (see above).
2. Reload scripts via hotkey or restart the game if it is already running.
3. Logging starts automatically once the player enters **Story Mode**.

### Building from source
- Visual Studio **2019 or newer**.
- Open `mod/src/GTALogger.sln`.
- Set references to `ScriptHookVDotNet3.dll` (and related SHVDN binaries).
- Adjust post‑build events to copy the compiled DLL to the game’s `scripts/` folder (and/or to `mod/bin/scripts/`).

---

## Output format (CSV)

Each received line corresponds to a game event / sample and is appended to the current CSV. A typical downstream dataset uses 8 columns:

- `char`, `time_ingame`, `time_rw`, `pos`, `vehicle`, `subtitles_text`, `speaker`, `soundfile`

The exact schema of your pipeline may extend this set (see the dataset repository for details).

---

## Troubleshooting

- **No data in CSV:** verify the local server is running and reachable; check firewall and that the mod loaded (ScriptHookVDotNet log).
- **Crashes on startup:** confirm ScriptHookV and ScriptHookVDotNet versions match the current game build.
- **Hot‑reload doesn’t work:** ensure `ReloadKeyBinding` is configured and focus is on the game.

---

## Credits & licenses

- ScriptHookVDotNet is distributed under the **zlib** license; if you include its binaries, keep `LICENSE.txt` alongside.
- ScriptHookV is a third‑party binary distributed from the official site above.
- The GTA V logging mod included here was originally authored by [**<Eduard Sariiev>**](https://github.com/eduard-sariiev) and is used with attribution.