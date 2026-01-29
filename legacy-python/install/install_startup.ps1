# PowerShell script to install Salah Widget to Windows Startup
# Run this script as Administrator for best results

Write-Host "=== Salah Widget Startup Installer ===" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$vbsPath = Join-Path $scriptPath "start_widget.vbs"
$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder "SalahWidget.lnk"

Write-Host "Script location: $scriptPath" -ForegroundColor Yellow
Write-Host "VBS file: $vbsPath" -ForegroundColor Yellow
Write-Host "Startup folder: $startupFolder" -ForegroundColor Yellow
Write-Host ""

# Method 1: Create a shortcut in the Startup folder
Write-Host "Creating startup shortcut..." -ForegroundColor Green

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$vbsPath`""
$Shortcut.WorkingDirectory = $scriptPath
$Shortcut.WindowStyle = 7
$Shortcut.Description = "Salah Times Widget"
$Shortcut.Save()

Write-Host "Shortcut created successfully!" -ForegroundColor Green
Write-Host "  Location: $shortcutPath" -ForegroundColor Gray
Write-Host ""

# Verify installation
if (Test-Path $shortcutPath) {
    Write-Host "=== Installation Complete ===" -ForegroundColor Cyan
    Write-Host "The Salah Widget will now start automatically when you log in to Windows." -ForegroundColor Green
    Write-Host ""
    Write-Host "To test, you can:" -ForegroundColor Yellow
    Write-Host "  1. Double-click the shortcut" -ForegroundColor Gray
    Write-Host "  2. Restart your computer" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To uninstall, run uninstall_startup.ps1" -ForegroundColor Yellow
} else {
    Write-Host "ERROR: Installation failed!" -ForegroundColor Red
    Write-Host "Please check permissions and try running as Administrator." -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
