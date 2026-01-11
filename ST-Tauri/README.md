# Salah Widget (Tauri Version)

This is a modern, high-performance desktop widget for prayer times, rebuilt using **Rust (Tauri)** and **React**.

## ✨ Features
- **Glassmorphism UI**: A sleek, modern design that fits perfectly on your desktop.
- **Auto-location**: Automatically detects your city and fetches prayer times.
- **Manual Search**: Add and switch between multiple locations.
- **Countdown**: Real-time countdown to the next prayer.
- **Lightweight**: Uses the native OS webview for minimal resource usage.

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: [Download here](https://nodejs.org/)
- **Rust Toolchain**: [Install via rustup](https://rustup.rs/)

### Installation & Development
1. **Clone and Navigate**:
   ```bash
   cd ST-Tauri
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Run in Development Mode**:
   ```bash
   npm run tauri dev
   ```

---

## 🛠 Building for Production

To create a standalone installer for Windows:

1. **Run the build command**:
   ```bash
   npm run tauri build
   ```

2. **Locate the Installer**:
   After the build completes, your installer will be located in:
   `src-tauri/target/release/bundle/nsis/st-tauri_0.1.0_x64-setup.exe`

3. **Install**:
   Run the generated `.exe` to install the widget on your system. It will appear in your applications list.

---

## 📂 Project Structure
- `src-tauri/`: The Rust backend logic (API calls, data processing).
- `src/`: The React frontend (UI components, styling, timers).

## 📄 License
MIT

