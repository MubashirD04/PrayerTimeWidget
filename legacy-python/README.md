# Salah Times Widget

A modern, aesthetic Windows desktop widget that displays Islamic prayer times for your location.

## Features

- **Real-time Prayer Times**: Automatically fetches accurate prayer times using the Aladhan API
- **Location Management**: Click the city name to switch between saved locations or add new ones
- **Countdown Timer**: Shows time remaining until the next prayer
- **Aesthetic Design**: Dark glassmorphism theme with smooth animations
- **Background Widget**: Stays on desktop without overlaying other apps
- **Draggable**: Position anywhere on your screen

## Installation

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the widget:
   ```
   python main.py
   ```

## Auto-Start on Windows Startup

To make the widget run automatically when Windows starts:

### Method 1: Automated Installer (Recommended)

1. Right-click on `install_startup.ps1`
2. Select **"Run with PowerShell"**
3. The script will automatically create a startup shortcut
4. Done! The widget will now start automatically when you log in

**To uninstall:** Right-click `uninstall_startup.ps1` and select "Run with PowerShell"

### Method 2: Manual Installation

1. Press `Win + R` to open the Run dialog
2. Type `shell:startup` and press Enter
3. Create a shortcut to `start_widget.vbs` in the Startup folder
4. The widget will now launch automatically on every Windows startup

> 📖 For detailed instructions and troubleshooting, see [STARTUP_INSTRUCTIONS.md](STARTUP_INSTRUCTIONS.md)

## Usage

### Changing Location
- Click on the city name at the top-left
- Select from saved locations or click "+ Add New Location"
- Enter a city name to search and add

### Deleting Locations
- Click the city name
- Click the **"×"** button next to any location to remove it (you must have more than one location saved to delete)

### Closing the Widget
- Right-click anywhere on the widget
- Select "Quit"

## Files

### Core Application
- `main.py` - Entry point
- `widget.py` - GUI implementation
- `prayer_api.py` - API logic for fetching prayer times
- `settings.json` - Stores your saved locations (auto-generated)

### Startup Files
- `start_widget.vbs` - Silent launcher (no console window)
- `start_widget.bat` - Alternative batch launcher
- `install_startup.ps1` - Automated startup installer
- `uninstall_startup.ps1` - Automated startup uninstaller
- `STARTUP_INSTRUCTIONS.md` - Detailed startup setup guide

## Customization

You can modify the appearance by editing the stylesheet values in `widget.py`:
- Background color/opacity
- Font sizes
- Border radius
- Colors

## Troubleshooting

**Widget doesn't show prayer times:**
- Check your internet connection
- The widget uses IP-based location detection on first run

**Location search doesn't work:**
- Try using full city names (e.g., "Makkah" instead of "Mecca")
- Check your internet connection

**Widget doesn't start on boot:**
- Verify `start_widget.vbs` is in the Startup folder
- Check that the path in `start_widget.vbs` matches your installation directory
