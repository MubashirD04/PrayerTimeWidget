mod prayer_api;
use prayer_api::{LocationData, PrayerTimes};

#[tauri::command]
async fn get_location_auto() -> Result<LocationData, String> {
    prayer_api::get_location().await
}

#[tauri::command]
async fn search_city(query: String) -> Result<LocationData, String> {
    prayer_api::search_location(&query).await
}

#[tauri::command]
async fn get_prayer_times_cmd(lat: f64, lon: f64) -> Result<PrayerTimes, String> {
    prayer_api::fetch_prayer_times(lat, lon).await
}

#[tauri::command]
async fn get_next_prayer_cmd(timings: PrayerTimes) -> (String, String, String) {
    prayer_api::get_next_prayer(&timings)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_autostart::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            #[cfg(desktop)]
            {
                use tauri_plugin_autostart::ManagerExt;
                let autostart_manager = app.autolaunch();
                let _ = autostart_manager.enable();
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_location_auto,
            search_city,
            get_prayer_times_cmd,
            get_next_prayer_cmd
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
