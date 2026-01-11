import sys
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QApplication, QMenu, QInputDialog, QMessageBox,
                             QWidgetAction, QPushButton)
from PyQt6.QtCore import Qt, QTimer, QTime, QPoint, QDate, QEvent
from PyQt6.QtGui import QFont, QColor, QPalette, QAction
from prayer_api import (get_location, fetch_prayer_times, get_next_prayer, 
                        format_countdown, search_location)
from datetime import datetime

SETTINGS_FILE = "settings.json"

STYLES = {
    "container": """
        #Container {
            background-color: rgba(20, 20, 25, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
        }
    """,
    "city_label": """
        color: #4da6ff; 
        font-size: 11px; 
        font-weight: bold; 
        letter-spacing: 1px;
        padding: 2px 5px;
    """,
    "clock_label": "color: #ffffff; font-size: 14px; font-weight: 500;",
    "next_name_label": "color: #cccccc; font-size: 16px; font-weight: bold; margin-top: 10px; letter-spacing: 2px;",
    "next_time_label": "color: #ffffff; font-size: 48px; font-weight: bold;",
    "countdown_label": "color: rgba(255, 255, 255, 0.7); font-size: 20px; font-weight: 500;",
    "separator": "background-color: rgba(255, 255, 255, 0.1); max-height: 1px;",
    "menu": """
        QMenu { background-color: #1a1a1f; color: white; border: 1px solid #333; border-radius: 8px; padding: 5px; }
        QMenu::item { padding: 8px 25px; border-radius: 4px; }
        QMenu::item:selected { background-color: #4da6ff; color: black; }
    """
}

class ClickableLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.parent_widget = parent
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.parent_widget:
                self.parent_widget.show_location_menu()
            event.accept()

class PrayerRow(QWidget):
    def __init__(self, name, time_str, is_next=False, is_completed=False, toggle_callback=None):
        super().__init__()
        self.name = name
        self.toggle_callback = toggle_callback
        self.is_completed = is_completed
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 8, 15, 8)
        self.setLayout(layout)
        
        color = "#ffffff" if is_next else "#bbbbbb"
        font_weight = QFont.Weight.Bold if is_next else QFont.Weight.Normal
        
        self.name_label = QLabel(name)
        self.update_style(color, font_weight)
        
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: {font_weight.value};")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(self.name_label)
        layout.addStretch()
        layout.addWidget(time_label)
        
        if is_next:
            self.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); border-radius: 10px;")
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def update_style(self, color, font_weight):
        style = f"color: {color}; font-size: 16px; font-weight: {font_weight.value};"
        if self.is_completed:
            style += " text-decoration: line-through;"
        self.name_label.setStyleSheet(style)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.toggle_callback:
                self.toggle_callback(self.name)
            event.accept()

class LocationMenuItem(QWidget):
    def __init__(self, name, is_active, parent_menu, select_cb, delete_cb=None):
        super().__init__()
        self.parent_menu = parent_menu
        self.select_cb = select_cb
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # Name Button
        self.name_btn = QPushButton(name)
        self.name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.name_btn.setStyleSheet(f"""
            text-align: left; 
            border: none; 
            background: transparent;
            font-size: 13px;
            color: {'#4da6ff' if is_active else '#ffffff'};
            font-weight: {'bold' if is_active else 'normal'};
        """)
        self.name_btn.clicked.connect(self.handle_select)
        layout.addWidget(self.name_btn, stretch=1)

        # Delete Button (if applicable)
        if delete_cb:
            self.del_btn = QPushButton("×")
            self.del_btn.setFixedSize(20, 20)
            self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.del_btn.setStyleSheet("""
                QPushButton { 
                    color: #666; 
                    border: none; 
                    border-radius: 10px; 
                    font-weight: bold; 
                    font-size: 16px;
                    background: transparent;
                }
                QPushButton:hover { 
                    background-color: #cc3333; 
                    color: white; 
                }
            """)
            self.del_btn.clicked.connect(lambda: [delete_cb(), self.parent_menu.close()])
            layout.addWidget(self.del_btn)

    def handle_select(self):
        self.select_cb()
        self.parent_menu.close()

class SalahWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.completed_prayers = set()
        self.last_date = QDate.currentDate()

        self.load_settings()
        self.prayer_times = fetch_prayer_times(self.lat, self.lon)
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_times)
        self.timer.start(1000)
        
        self.api_timer = QTimer(self)
        self.api_timer.timeout.connect(self.refresh_data)
        self.api_timer.start(3600000) 

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                self.settings = json.load(f)
        else:
            # Auto-detect on first run
            lat, lon, city = get_location()
            self.settings = {
                "active_location": {"name": city, "lat": lat, "lon": lon},
                "saved_locations": [{"name": city, "lat": lat, "lon": lon}]
            }
            self.save_settings()
        
        loc = self.settings["active_location"]
        self.lat, self.lon, self.city = loc["lat"], loc["lon"], loc["name"]

    def save_settings(self):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def init_ui(self):
        # Removed WindowStaysOnTopHint as requested
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(self.main_layout)
        
        self.container = QFrame()
        self.container.setObjectName("Container")
        self.container.setStyleSheet(STYLES["container"])
        container_layout = QVBoxLayout()
        container_layout.setSpacing(15)
        self.container.setLayout(container_layout)
        self.main_layout.addWidget(self.container)
        
        # 1. Header
        header_layout = QHBoxLayout()
        
        self.city_label = ClickableLabel(self.city.upper(), self)
        self.city_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.city_label.setStyleSheet(STYLES["city_label"])
        
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(STYLES["clock_label"])
        
        header_layout.addWidget(self.city_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clock_label)
        container_layout.addLayout(header_layout)
        
        # 2. Hero Section
        hero_layout = QVBoxLayout()
        hero_layout.setSpacing(2)
        
        self.next_name_label = QLabel("NEXT PRAYER")
        self.next_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_name_label.setStyleSheet(STYLES["next_name_label"])
        
        self.next_time_label = QLabel("--:--")
        self.next_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_time_label.setStyleSheet(STYLES["next_time_label"])
        
        self.countdown_label = QLabel("--")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet(STYLES["countdown_label"])
        
        hero_layout.addWidget(self.next_name_label)
        hero_layout.addWidget(self.next_time_label)
        hero_layout.addWidget(self.countdown_label)
        container_layout.addLayout(hero_layout)
        
        # 3. Separator and List (Collapsible)
        self.toggle_frame = QFrame()
        self.toggle_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_frame.setFixedHeight(20)
        toggle_layout = QVBoxLayout(self.toggle_frame)
        toggle_layout.setContentsMargins(0, 5, 0, 5)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(STYLES["separator"])
        toggle_layout.addWidget(line)
        
        self.container.layout().addWidget(self.toggle_frame)
        self.toggle_frame.mousePressEvent = self.toggle_expanded

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(5)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.container.layout().addWidget(self.list_container)
        
        # Initial State: Hidden
        self.expanded = False
        self.list_container.setVisible(False)
        
        self.update_times()
        self.setFixedWidth(320)

    def toggle_expanded(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.expanded = not self.expanded
            
            if self.expanded:
                self.list_container.setVisible(True)
                self.update_times()
            else:
                self.list_container.setVisible(False)

            QApplication.processEvents()
            self.adjustSize()
            self.setFixedWidth(320)  # Ensure width stays consistent
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1e1e24; color: white; border: 1px solid #333; }
            QMenu::item:selected { background-color: #3e3e4a; }
        """)
        quit_action = menu.addAction("Quit")
        action = menu.exec(event.globalPos())
        if action == quit_action:
            QApplication.quit()

    def show_location_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(STYLES["menu"])
        
        # Saved locations
        for i, loc in enumerate(self.settings["saved_locations"]):
            is_active = (loc["name"] == self.city)
            can_delete = (len(self.settings["saved_locations"]) > 1)
            
            # Callback wrappers
            select_cb = lambda l=loc: self.set_active_location(l)
            delete_cb = (lambda idx=i: self.delete_location(idx)) if can_delete else None
            
            # Create custom action
            item_widget = LocationMenuItem(loc["name"], is_active, menu, select_cb, delete_cb)
            action = QWidgetAction(menu)
            action.setDefaultWidget(item_widget)
            menu.addAction(action)
            
        menu.addSeparator()
        add_action = menu.addAction("+ Add New Location")
        add_action.triggered.connect(self.add_location_dialog)
        
        menu.exec(self.city_label.mapToGlobal(QPoint(0, self.city_label.height())))

    def set_active_location(self, loc):
        self.settings["active_location"] = loc
        self.lat, self.lon, self.city = loc["lat"], loc["lon"], loc["name"]
        self.city_label.setText(self.city.upper())
        self.save_settings()
        self.refresh_data()

    def add_location_dialog(self):
        city_name, ok = QInputDialog.getText(self, "Add Location", "Enter city name:")
        if ok and city_name:
            res = search_location(city_name)
            if res:
                lat, lon, name = res
                new_loc = {"name": name, "lat": lat, "lon": lon}
                # Check if already exists
                if not any(l["name"] == name for l in self.settings["saved_locations"]):
                    self.settings["saved_locations"].append(new_loc)
                    self.set_active_location(new_loc)
                else:
                    self.set_active_location(next(l for l in self.settings["saved_locations"] if l["name"] == name))
            else:
                QMessageBox.warning(self, "Error", "Could not find location.")

    def delete_location(self, index):
        loc_to_del = self.settings["saved_locations"].pop(index)
        if self.settings["active_location"]["name"] == loc_to_del["name"]:
            # Switch to first available
            self.set_active_location(self.settings["saved_locations"][0])
        else:
            self.save_settings()

    def refresh_data(self):
        self.prayer_times = fetch_prayer_times(self.lat, self.lon)
        self.update_times()

    def toggle_prayer_completion(self, prayer_name):
        if prayer_name in self.completed_prayers:
            self.completed_prayers.remove(prayer_name)
        else:
            self.completed_prayers.add(prayer_name)
        self.update_times()

    def update_times(self):
        now = QDate.currentDate()
        if now != self.last_date:
            self.completed_prayers.clear()
            self.last_date = now
            self.refresh_data()  # Fetch new times for the new day

        curr_time = QTime.currentTime().toString("HH:mm")
        self.clock_label.setText(curr_time)
        
        if not self.prayer_times:
            return
            
        next_p_name, next_p_datetime = get_next_prayer(self.prayer_times)
        remaining = next_p_datetime - datetime.now()
        
        self.next_name_label.setText(next_p_name.upper())
        self.next_time_label.setText(next_p_datetime.strftime("%H:%M"))
        self.countdown_label.setText(format_countdown(remaining))
        
        # Only populate the list if expanded
        if self.expanded:
            for i in reversed(range(self.list_layout.count())): 
                widget = self.list_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
                
            prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
            for p in prayers:
                p_time = self.prayer_times[p]
                is_next = (p == next_p_name)
                is_completed = (p in self.completed_prayers)
                self.list_layout.addWidget(PrayerRow(p, p_time, is_next, is_completed, self.toggle_prayer_completion))
            
            self.list_container.show()
        else:
            self.list_container.hide()
            
        self.resize(320, self.minimumSizeHint().height())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)
            event.accept()
