import { useState, useEffect, useRef } from 'react';
import { api, LocationData, PrayerTimes } from './api';
import './App.css';
import { getCurrentWindow } from '@tauri-apps/api/window'; // For drag if needed, or use data-tauri-drag-region

function App() {
  const [location, setLocation] = useState<LocationData | null>(null);
  const [prayerTimes, setPrayerTimes] = useState<PrayerTimes | null>(null);
  const [nextPrayer, setNextPrayer] = useState<{ name: string, time: string, countdown: string }>({ name: '--', time: '--:--', countdown: '--' });
  const [currentTime, setCurrentTime] = useState<string>('--:--');
  const [expanded, setExpanded] = useState(false);
  const [completedPrayers, setCompletedPrayers] = useState<Set<string>>(new Set());
  const [showMenu, setShowMenu] = useState(false);
  const dataRef = useRef<{ times: PrayerTimes | null }>({ times: null });

  // Initial Load
  useEffect(() => {
    initApp();

    // Timer for clock and countdown
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const initApp = async () => {
    // TODO: Load from validation/persistence if needed
    // For now, auto-detect
    try {
      const loc = await api.getLocationAuto();
      setLocation(loc);
      await refreshData(loc.lat, loc.lon);
    } catch (e) {
      console.error(e);
    }
  };

  const refreshData = async (lat: number, lon: number) => {
    try {
      const times = await api.getPrayerTimes(lat, lon);
      setPrayerTimes(times);
      dataRef.current.times = times;
      updateTime();
    } catch (e) {
      console.error(e);
    }
  };

  const updateTime = async () => {
    const now = new Date();
    setCurrentTime(now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }));

    if (dataRef.current.times) {
      const [name, time, diff] = await api.getNextPrayer(dataRef.current.times);
      setNextPrayer({ name, time, countdown: diff });
    }
  };

  const toggleComplete = (name: string) => {
    const newSet = new Set(completedPrayers);
    if (newSet.has(name)) newSet.delete(name);
    else newSet.add(name);
    setCompletedPrayers(newSet);
  };

  const handleAddLocation = async () => {
    const city = prompt("Enter city name:");
    if (city) {
      try {
        const res = await api.searchCity(city);
        setLocation(res);
        await refreshData(res.lat, res.lon);
        setShowMenu(false);
      } catch (e) {
        alert("Location not found");
      }
    }
  };

  const prayerOrder = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];

  return (
    <div className="widget-container" data-tauri-drag-region>
      {/* Header */}
      <div className="header" data-tauri-drag-region>
        <div
          className="city-badge"
          onClick={() => setShowMenu(!showMenu)}
        >
          {location?.city.toUpperCase() || "LOADING..."}
        </div>
        <div className="clock">{currentTime}</div>
      </div>

      {/* Menu Overlay */}
      {showMenu && (
        <div className="location-menu">
          <div className="menu-item active">
            {location?.city}
            <span className="close-btn" onClick={() => setShowMenu(false)}>×</span>
          </div>
          {/* Saved locations list would go here */}
          <div className="menu-item" onClick={handleAddLocation}>+ Add Location</div>
          <div className="menu-item" onClick={() => getCurrentWindow().close()}>Quit</div>
        </div>
      )}

      {/* Hero */}
      <div className="hero" data-tauri-drag-region>
        <div className="next-label">NEXT PRAYER</div>
        <div className="next-time">{nextPrayer.time}</div>
        <div className="countdown">{nextPrayer.countdown}</div>
      </div>

      {/* Toggle / List */}
      <div className="divider" onClick={() => setExpanded(!expanded)}></div>

      {expanded && prayerTimes && (
        <div className="prayer-list">
          {prayerOrder.map(key => {
            const time = prayerTimes[key as keyof PrayerTimes];
            const isNext = key === nextPrayer.name;
            const isCompleted = completedPrayers.has(key);

            return (
              <div
                key={key}
                className={`prayer-row ${isNext ? 'next' : ''} ${isCompleted ? 'completed' : ''}`}
                onClick={() => toggleComplete(key)}
              >
                <span className="prayer-name">{key}</span>
                <span className="prayer-time">{time}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default App;
