# jrnl-lncher

<video src="media/jrnl-lnchr-recording-web.mp4" controls autoplay muted loop></video>

A minimalist, high-speed Windows utility to quickly add entries to your [jrnl](https://jrnl.sh/) using a global hotkey.

## Features

- **Global Hotkey (`Win + J`)**: Instantly pops up a minimalist entry window.
- **Collapsible History**: View your last 3 journal entries with a single click on the toggle arrow.
- **Smart Focus**: Automatically focuses the text box so you can start typing immediately.
- **Modern UI**: Dark-themed, borderless window with rounded corners.
- **Lightweight**: Built with Python and Tkinter for near-zero lag.
- **Background Service**: Runs silently in the background and starts automatically with Windows.

## Controls

- **Enter**: Save your entry and hide the window.
- **Shift + Enter**: Add a new line within your entry.
- **Escape**: Hide the window without saving.
- **▲ / ▼ Arrow**: Toggle the display of your recent journal history.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for fast Python dependency management.

1.  **Install dependencies**:
    ```bash
    uv sync
    ```
2.  **Configure your environment**:
    Copy `.env.example` to `.env` and adjust as needed:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` to set your preferred hotkey (default is `Win + J`).
3.  **Run the service**:
    ```bash
    uv run python main.py
    ```
4.  **Automatic Startup**:
    Run the included `setup_startup.ps1` PowerShell script to add the utility to your Windows Startup folder:
    ```powershell
    powershell -ExecutionPolicy Bypass -File setup_startup.ps1
    ```

## Requirements

- Windows 10/11
- [jrnl](https://jrnl.sh/) installed and configured in your PATH.
- [uv](https://github.com/astral-sh/uv) for Python management.
