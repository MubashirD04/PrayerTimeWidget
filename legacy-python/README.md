# Salah Tracker (Legacy Python Version)

This directory contains the original version of the Salah Tracker, built using **Python** and **Tkinter**.

## Overview
This version was the initial implementation of the prayer time widget before the project transitioned to Rust and Tauri. It uses standard Python libraries to fetch prayer times and display them in a desktop-integrated window.

## Main Components
- `widget.py`: The core UI implementation using Tkinter.
- `main.py`: The entry point for the application.
- `prayer_api.py`: Handles fetching prayer times from external APIs.
- `settings.json`: Stores user preferences and location data.
- `prayer_cache.json`: Local cache for prayer times.

## How to Run (Legacy)
If you still wish to run this version, ensure you have Python installed and run:
```bash
pip install -r requirements.txt
python main.py
```

## Status
This version is currently in **maintenance mode**. All new feature development and active improvements are happening in the root directory's Rust implementation.
