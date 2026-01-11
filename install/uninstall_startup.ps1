# PowerShell script to remove Salah Widget from Windows Startup

Write-Host "=== Salah Widget Startup Uninstaller ===" -ForegroundColor Cyan
Write-Host ""

$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder "SalahWidget.lnk"

if (Test-Path $shortcutPath) {
    Write-Host "Removing startup shortcut..." -ForegroundColor Yellow
    Remove-Item $shortcutPath -Force
    Write-Host "Shortcut removed successfully!" -ForegroundColor Green
    Write-Host "The Salah Widget will no longer start automatically." -ForegroundColor Gray
} else {
    Write-Host "No startup shortcut found." -ForegroundColor Yellow
    Write-Host "The widget is not currently set to auto-start." -ForegroundColor Gray
}

Write-Host ""
Read-Host "Press Enter to exit"
