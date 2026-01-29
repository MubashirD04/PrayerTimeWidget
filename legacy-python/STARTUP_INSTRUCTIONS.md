# Salah Widget - Auto-Start Setup Instructions

This guide will help you set up the Salah Widget to start automatically when Windows boots.

## Quick Installation (Recommended)

### Method 1: Using PowerShell Installer (Easiest)

1. **Right-click** on `install_startup.ps1`
2. Select **"Run with PowerShell"**
3. If prompted about execution policy, type `Y` and press Enter
4. The script will create a shortcut in your Startup folder
5. Done! The widget will now start automatically when you log in

### Method 2: Manual Installation

1. Press `Win + R` to open Run dialog
2. Type `shell:startup` and press Enter
3. This opens your Startup folder
4. Create a shortcut to `start_widget.vbs` in this folder
5. Done!

## Verification

To verify the installation worked:

1. Check your Startup folder (`Win + R` → `shell:startup`)
2. You should see a shortcut named "SalahWidget"
3. Double-click it to test - the widget should appear
4. Restart your computer to test auto-start

## Uninstallation

### Using PowerShell Uninstaller

1. **Right-click** on `uninstall_startup.ps1`
2. Select **"Run with PowerShell"**
3. The startup shortcut will be removed

### Manual Uninstallation

1. Press `Win + R` → type `shell:startup` → press Enter
2. Delete the "SalahWidget" shortcut
3. Done!

## Troubleshooting

### Widget doesn't start on boot

1. **Check Python installation**: Make sure Python is installed and in your PATH
2. **Test manually**: Double-click `start_widget.vbs` to see if it works
3. **Check Startup folder**: Ensure the shortcut exists in `shell:startup`
4. **Check file paths**: Open `start_widget.vbs` and verify the path is correct

### Widget starts but crashes immediately

1. **Check dependencies**: Run `pip install -r requirements.txt`
2. **Test manually**: Run `python main.py` from command line to see errors
3. **Check settings**: Ensure `settings.json` is valid or delete it to regenerate

### Multiple instances running

1. The widget doesn't prevent multiple instances
2. Check Task Manager and close extra instances
3. Make sure you only have one startup entry

## Alternative: Task Scheduler (Advanced)

For more control, you can use Windows Task Scheduler:

1. Open Task Scheduler (`Win + R` → `taskschd.msc`)
2. Click "Create Basic Task"
3. Name: "Salah Widget"
4. Trigger: "When I log on"
5. Action: "Start a program"
6. Program: `wscript.exe`
7. Arguments: `"C:\Users\mubas\OneDrive\Desktop\Projects\Python\ST\start_widget.vbs"`
8. Finish and test

## Files Explained

- **`start_widget.vbs`**: VBScript that starts the widget silently (no console window)
- **`start_widget.bat`**: Alternative batch file (shows console briefly)
- **`install_startup.ps1`**: Automated installer for Windows Startup
- **`uninstall_startup.ps1`**: Automated uninstaller
- **`main.py`**: The main widget application

## Notes

- The widget uses `pythonw.exe` (via VBS) to run without a console window
- The widget will remember your location settings between restarts
- You can move the widget by dragging it with your mouse
- Right-click the widget to quit it
