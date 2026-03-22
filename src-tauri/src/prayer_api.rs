use chrono::{Local, NaiveTime};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PrayerTimes {
    #[serde(rename = "Fajr")]
    pub fajr: String,
    #[serde(rename = "Dhuhr")]
    pub dhuhr: String,
    #[serde(rename = "Asr")]
    pub asr: String,
    #[serde(rename = "Maghrib")]
    pub maghrib: String,
    #[serde(rename = "Isha")]
    pub isha: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct LocationData {
    pub lat: f64,
    pub lon: f64,
    pub city: String,
}

#[derive(Deserialize, Debug)]
struct IpApiResponse {
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub city: Option<String>,
}

#[derive(Deserialize, Debug)]
struct AladhanCalendarResponse {
    data: Vec<AladhanDayData>,
}

#[derive(Deserialize, Debug)]
struct AladhanDayData {
    timings: HashMap<String, String>,
    date: AladhanDateInfo,
}

#[derive(Deserialize, Debug)]
struct AladhanDateInfo {
    gregorian: GregorianDateInfo,
}

#[derive(Deserialize, Debug)]
struct GregorianDateInfo {
    date: String, // "DD-MM-YYYY"
}

#[derive(Deserialize, Debug)]
struct ArcGisResponse {
    candidates: Vec<ArcGisCandidate>,
}

#[derive(Deserialize, Debug)]
struct ArcGisCandidate {
    address: String,
    location: ArcGisLocation,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct CacheEntry {
    date: String,
    lat: f64,
    lon: f64,
    timings: PrayerTimes,
}

#[derive(Serialize, Deserialize, Debug, Default)]
struct CacheStore {
    entries: Vec<CacheEntry>,
}

fn get_cache_path() -> std::path::PathBuf {
    let mut path = std::env::temp_dir();
    path.push("st_prayer_cache_v2.json");
    path
}

fn load_store() -> CacheStore {
    let path = get_cache_path();
    if let Ok(content) = std::fs::read_to_string(path) {
        if let Ok(store) = serde_json::from_str::<CacheStore>(&content) {
            return store;
        }
    }
    CacheStore::default()
}

fn save_store(store: &CacheStore) {
    let path = get_cache_path();
    if let Ok(json) = serde_json::to_string(store) {
        let _ = std::fs::write(path, json);
    }
}

fn load_cache(lat: f64, lon: f64) -> Option<PrayerTimes> {
    let store = load_store();
    let today = Local::now().format("%Y-%m-%d").to_string();
    
    for entry in store.entries {
        if entry.date == today 
           && (entry.lat - lat).abs() < 0.1 
           && (entry.lon - lon).abs() < 0.1 {
            return Some(entry.timings);
        }
    }
    None
}

fn save_cache_batch(lat: f64, lon: f64, batch: Vec<CacheEntry>) {
    let mut store = load_store();
    let today = Local::now().format("%Y-%m-%d").to_string();
    
    // Cleanup: Remove old dates (anything before today)
    // AND remove any existing entries for this location that are about to be replaced by the new batch
    let batch_dates: std::collections::HashSet<String> = batch.iter().map(|e| e.date.clone()).collect();
    
    store.entries.retain(|e| {
        let is_same_loc = (e.lat - lat).abs() < 0.1 && (e.lon - lon).abs() < 0.1;
        let is_past = e.date < today;
        let is_in_batch = batch_dates.contains(&e.date);
        
        !is_past && !(is_same_loc && is_in_batch)
    });

    store.entries.extend(batch);
    save_store(&store);
}

#[derive(Deserialize, Debug)]
struct ArcGisLocation {
    x: f64, // lon
    y: f64, // lat
}

pub async fn get_location() -> Result<LocationData, String> {
    let client = Client::new();

    // Source 1: ip-api.com
    // Source 1: ip-api.com (https version requires pro, but let's try or stick to a better one)
    // Actually, ip-api.com https is paid. 
    // Let's use ipapi.co (secure and free for basic usage)
    match client.get("https://ipapi.co/json/").send().await {
        Ok(resp) => {
            if let Ok(data) = resp.json::<IpApiResponse>().await {
                if let (Some(lat), Some(lon), Some(city)) = (data.latitude, data.longitude, data.city) {
                    return Ok(LocationData { lat, lon, city });
                }
            }
        }
        Err(e) => println!("ipapi.co failed: {}", e),
    }

    // Fallback: London
    Ok(LocationData {
        lat: 51.5074,
        lon: -0.1278,
        city: "London".to_string(),
    })
}

pub async fn search_location(query: &str) -> Result<LocationData, String> {
    let client = Client::new();
    let url =
        "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates";

    let params = [("f", "json"), ("singleLine", query), ("maxLocations", "1")];

    match client.get(url).query(&params).send().await {
        Ok(resp) => {
            if let Ok(data) = resp.json::<ArcGisResponse>().await {
                if let Some(candidate) = data.candidates.first() {
                    return Ok(LocationData {
                        lat: candidate.location.y,
                        lon: candidate.location.x,
                        city: candidate.address.clone(),
                    });
                }
            }
        }
        Err(e) => return Err(format!("Search request failed: {}", e)),
    }

    Err("Location not found".to_string())
}

pub async fn fetch_prayer_times(lat: f64, lon: f64) -> Result<PrayerTimes, String> {
    // 1. Check cache for today
    if let Some(cached) = load_cache(lat, lon) {
        println!("Using cached prayer times");
        return Ok(cached);
    }

    let client = Client::new();
    let now = Local::now();
    let month = now.format("%m").to_string();
    let year = now.format("%Y").to_string();
    
    let url = format!(
        "https://api.aladhan.com/v1/calendar?latitude={}&longitude={}&method=2&month={}&year={}",
        lat, lon, month, year
    );

    match client.get(&url).send().await {
        Ok(resp) => match resp.json::<AladhanCalendarResponse>().await {
            Ok(data) => {
                let mut batch = Vec::new();
                let today_str = now.format("%Y-%m-%d").to_string();
                let mut today_timings = None;

                for day in data.data {
                    let t = day.timings;
                    let timings = PrayerTimes {
                        fajr: t.get("Fajr").unwrap_or(&"00:00".to_string()).clone(),
                        dhuhr: t.get("Dhuhr").unwrap_or(&"00:00".to_string()).clone(),
                        asr: t.get("Asr").unwrap_or(&"00:00".to_string()).clone(),
                        maghrib: t.get("Maghrib").unwrap_or(&"00:00".to_string()).clone(),
                        isha: t.get("Isha").unwrap_or(&"00:00".to_string()).clone(),
                    };
                    
                    // Aladhan date format is DD-MM-YYYY, convert to YYYY-MM-DD for consistency
                    let components: Vec<&str> = day.date.gregorian.date.split('-').collect();
                    if components.len() == 3 {
                        let iso_date = format!("{}-{}-{}", components[2], components[1], components[0]);
                        
                        if iso_date == today_str {
                            today_timings = Some(timings.clone());
                        }
                        
                        batch.push(CacheEntry {
                            date: iso_date,
                            lat,
                            lon,
                            timings,
                        });
                    }
                }
                
                // 2. Save entire month to cache
                save_cache_batch(lat, lon, batch);
                
                today_timings.ok_or_else(|| "Could not find today in calendar".to_string())
            }
            Err(e) => Err(format!("Failed to parse calendar times: {}", e)),
        },
        Err(e) => Err(format!("API Request failed: {}", e)),
    }
}

pub fn get_next_prayer(timings: &PrayerTimes) -> (String, String, String) {
    // Returns (Next Prayer Name, Time String, Countdown String)
    let now = Local::now();

    let prayers = vec![
        ("Fajr", &timings.fajr),
        ("Dhuhr", &timings.dhuhr),
        ("Asr", &timings.asr),
        ("Maghrib", &timings.maghrib),
        ("Isha", &timings.isha),
    ];

    let mut next_prayer = None;

    for (name, time_str) in &prayers {
        // time_str is "HH:MM"
        if let Ok(time) = NaiveTime::parse_from_str(time_str, "%H:%M") {
            let prayer_dt = now
                .date_naive()
                .and_time(time)
                .and_local_timezone(Local)
                .unwrap();

            if prayer_dt > now {
                let diff = prayer_dt - now;
                next_prayer = Some((
                    name.to_string(),
                    time_str.to_string(),
                    format_duration(diff),
                ));
                break;
            }
        }
    }

    if let Some(res) = next_prayer {
        res
    } else {
        // Next is Fajr tomorrow
        let (name, time_str) = prayers[0];
        // Simple calc - technically need proper date math but for display:
        // Assume tomorrow's fajr is same time
        if let Ok(time) = NaiveTime::parse_from_str(time_str, "%H:%M") {
            let tomorrow = now.date_naive().succ_opt().unwrap();
            let prayer_dt = tomorrow.and_time(time).and_local_timezone(Local).unwrap();
            let diff = prayer_dt - now;
            (
                name.to_string(),
                time_str.to_string(),
                format_duration(diff),
            )
        } else {
            ("Fajr".to_string(), time_str.to_string(), "--".to_string())
        }
    }
}

fn format_duration(dur: chrono::Duration) -> String {
    let seconds = dur.num_seconds();
    let h = seconds / 3600;
    let m = (seconds % 3600) / 60;
    if h > 0 {
        format!("{}h {}m", h, m)
    } else {
        format!("{}m", m)
    }
}
