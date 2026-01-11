import sys
import os

# Add parent directory to path to import widget
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from widget import SalahWidget, PrayerRow

def test_strikethrough():
    app = QApplication(sys.argv)
    widget = SalahWidget()
    
    # Mock data to ensure we have prayers
    widget.prayer_times = {
        "Fajr": "05:00",
        "Dhuhr": "12:00",
        "Asr": "15:00",
        "Maghrib": "18:00",
        "Isha": "20:00"
    }
    
    # Force expand to populate list
    widget.expanded = True
    widget.update_times()
    
    # Find a prayer row (e.g., Fajr)
    fajr_row = None
    for i in range(widget.list_layout.count()):
        item = widget.list_layout.itemAt(i)
        if item.widget() and isinstance(item.widget(), PrayerRow):
            row = item.widget()
            if row.name_label.text() == "Fajr":
                fajr_row = row
                break
    
    if not fajr_row:
        print("FAIL: Fajr row not found")
        return

    print("Checking initial state...")
    if "line-through" in fajr_row.name_label.styleSheet():
         print("FAIL: Initial state has line-through")
    else:
         print("PASS: Initial state correct")

    print("Simulating toggle...")
    # Simulate click logic (calling the callback directly as we can't easily fake mouse events in headless without more setup)
    widget.toggle_prayer_completion("Fajr")
    
    # Re-find the row as update_times clears and recreates them
    fajr_row = None
    for i in range(widget.list_layout.count()):
        item = widget.list_layout.itemAt(i)
        if item.widget() and isinstance(item.widget(), PrayerRow):
            row = item.widget()
            if row.name_label.text() == "Fajr":
                fajr_row = row
                break
                
    if not fajr_row:
        print("FAIL: Fajr row not found after update")
        return

    print("Checking toggled state...")
    if "line-through" in fajr_row.name_label.styleSheet():
         print("PASS: Toggled state has line-through")
    else:
         print("FAIL: Toggled state missing line-through")

    print("Simulating persistency...")
    widget.update_times()
    
    # Re-find again
    fajr_row = None
    for i in range(widget.list_layout.count()):
        item = widget.list_layout.itemAt(i)
        if item.widget() and isinstance(item.widget(), PrayerRow):
            row = item.widget()
            if row.name_label.text() == "Fajr":
                fajr_row = row
                break
    
    if "line-through" in fajr_row.name_label.styleSheet():
         print("PASS: State persisted after update")
    else:
         print("FAIL: State lost after update")

    print("Test Complete")

if __name__ == "__main__":
    test_strikethrough()
