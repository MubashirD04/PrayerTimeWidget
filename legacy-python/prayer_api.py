import requests
import geocoder
import json
import os
from datetime import datetime, timedelta

CACHE_FILE = "prayer_cache.json"

def get_location():
    """Returns (latitude, longitude, city) using multiple sources"""
    # Try Source 1: ip-api.com (Reliable, no key)
    try:
        resp = requests.get("http://ip-api.com/json", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data['status'] == 'success':
                return data['lat'], data['lon'], data['city']
    except Exception as e:
        print(f"Source 1 failed: {e}")

    # Try Source 2: geocoder (ipinfo.io fallback)
    try:
        g = geocoder.ip('me')
        if g.latlng:
            return g.latlng[0], g.latlng[1], g.city or "Unknown"
    except Exception as e:
        print(f"Source 2 failed: {e}")

    # Default to London if all else fails
    print("Using default location (London)")
    return 51.5074, -0.1278, "London"

def search_location(query):
    """Searches for a location and returns (lat, lon, city) or None"""
    try:
        g = geocoder.arcgis(query)
        if g.ok:
            # ArcGIS returns city in g.city, fallback to g.address
            return g.lat, g.lng, g.city or g.address
    except Exception as e:
        print(f"Search failed: {e}")
    return None

def fetch_prayer_times(lat, lon):
    """Fetches prayer times for today from Aladhan API or local cache (keeps top 2 locations)"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    # Round lat/lon to 4 decimal places for consistent cache keys
    cache_key = f"{round(float(lat), 4)},{round(float(lon), 4)},{today_str}"
    
    current_cache = {"locations": []}

    # 1. Load Cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                # Handle migration from old single-object cache if necessary
                if "locations" in data:
                    current_cache = data
                elif "key" in data: # Old format
                    current_cache["locations"].append(data)
        except Exception as e:
            print(f"Cache read error: {e}")

    # 2. Check for key in cache locations
    locations = current_cache["locations"]
    for i, loc in enumerate(locations):
        if loc.get("key") == cache_key:
            # Move to front (LRU)
            locations.insert(0, locations.pop(i))
            # Save back to ensure order updates
            try:
                with open(CACHE_FILE, 'w') as f:
                    json.dump(current_cache, f)
            except: pass
            return loc["data"]

    # 3. Fetch from API
    try:
        # Using method 2 (Islamic Society of North America) as a default, 
        # but the API allows many methods.
        url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=2"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            timings = data['data']['timings']
            
            # 4. Save to Cache
            new_entry = {"key": cache_key, "data": timings}
            locations.insert(0, new_entry)
            
            # Keep only top 2
            if len(locations) > 2:
                locations = locations[:2]
            
            current_cache["locations"] = locations
            
            try:
                with open(CACHE_FILE, 'w') as f:
                    json.dump(current_cache, f)
            except Exception as e:
                print(f"Cache write error: {e}")
                
            return timings
    except Exception as e:
        print(f"Error fetching prayer times: {e}")
    return None

def get_next_prayer(timings):
    """
    Identifies the next prayer and time remaining.
    Timings is a dict: {'Fajr': '05:30', ...}
    """
    now = datetime.now()
    # prayers to track
    prayer_names = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    
    prayer_list = []
    today = now.date()
    
    for name in prayer_names:
        time_str = timings[name]
        hour, minute = map(int, time_str.split(':'))
        pray_time = datetime.combine(today, datetime.min.time()).replace(hour=hour, minute=minute)
        prayer_list.append((name, pray_time))
        
    # Sort just in case (though Aladhan is sorted)
    prayer_list.sort(key=lambda x: x[1])
    
    next_p = None
    for name, p_time in prayer_list:
        if p_time > now:
            next_p = (name, p_time)
            break
            
    if not next_p:
        # If all prayers today are passed, the next is Fajr tomorrow
        name, p_time = prayer_list[0]
        next_p = (name, p_time + timedelta(days=1))
        
    return next_p

def format_countdown(td):
    """Formats a timedelta as Hh Mm"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
