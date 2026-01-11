import sys
from PyQt6.QtWidgets import QApplication
from widget import SalahWidget

def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font if possible
    # app.setFont(QFont("Segoe UI", 10)) 
    
    try:
        window = SalahWidget()
        # Initial position (top right corner roughly)
        screen = app.primaryScreen().geometry()
        window.move(screen.width() - window.width() - 50, 50)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Failed to start Salah Widget: {e}")

if __name__ == "__main__":
    main()
