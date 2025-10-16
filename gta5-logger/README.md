# World Logging

A lightweight setup for logging in‑game data to CSV. The repository has two parts:

- **Game Mod** (C#, SHVDN) that emits log lines.
- **Local Server** (Python, aiohttp) that receives lines and appends them to a timestamped CSV file.


```
.
├── local_server/                # Logging server
│   ├── requirements.txt         # 
│   ├── server.py                # 
│   ├── start.bat                # 
│   └── start.sh                 # 
└── mod/                         # Game mod
    ├── src/                     # Mod source (ScriptHookVDotNet / C#)
    ├── prerequisites/           # Deps
    └── bin/                     # Binary
        └── scripts/             
```

---

## Logging server

### Requirements
- Python 3.8+
- Install Python deps:
  ```bash
  pip install -r local_server/requirements.txt
  ```

### Running
Server can be started either directly or via helper scripts:

- **Direct (CLI):**
  ```bash
  cd local_server
  python server.py --host 0.0.0.0 --port 8080
  ```

- **Helper script (Windows):**
  ```bash
  start.bat
  ```

- **Helper script (Linux/macOS):**
  ```bash
  ./start.sh
  ```

### CLI Arguments
- `--host` (or `-H`): address to bind to (e.g., `127.0.0.1`, `0.0.0.0`).
- `--port` (or `-P`): port number (default `8080`).

> The server writes all received lines to a CSV file named after the **server start timestamp**, e.g. `received_YYYYMMDD_HHMMSS_mmmmmm.csv`.

---

## Mod

### Preparation
- Make sure both [Microsoft .NET Framework 4.8 ](https://dotnet.microsoft.com/download/dotnet-framework/net48) and [Microsoft Visual C++ Redistributable Package for Visual Studio 2019 (x64)](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads) are installed.
- Copy files from `mod/prerequisites` to game's folder root. *(Alternatively, follow instructions for [SHVDN-Nightly](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads) installation)*
- Run game once.
- *(optional)* Add key binding to reload scripts in `ScriptHookVDotNet.ini` at `ReloadKeyBinding`.

### Installation
- Copy `mod/scripts` folder to game's folder root.

### Running
- Start logging server mentioned above.
- Reload scripts using hotkey or restart the game if already running.
- Logging will start automatically once player is in story mode.


### Building from Source
- Visual Studio 2019 or newer
- Open `GTALogger.sln` project
- Edit references for `ScriptHookVDotNet3.dll`
- Change path in post-build events to copy compiled binary to game's scripts folder.

