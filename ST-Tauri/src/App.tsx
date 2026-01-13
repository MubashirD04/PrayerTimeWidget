import { useState, useEffect, useRef } from 'react';
import { getCurrentWindow, LogicalSize } from '@tauri-apps/api/window';
import { api, LocationData, PrayerTimes } from './api';
import './App.css';

function App() {
  /* Location State */
  const [location, setLocation] = useState<LocationData | null>(null);
  const [savedLocations, setSavedLocations] = useState<LocationData[]>(() => {
    const saved = localStorage.getItem('savedLocations');
    return saved ? JSON.parse(saved) : [];
  });

  /* Data State */
  const [prayerTimes, setPrayerTimes] = useState<PrayerTimes | null>(null);
  const [nextPrayer, setNextPrayer] = useState<{ name: string, time: string, countdown: string }>({ name: '--', time: '--:--', countdown: '--' });
  const [currentTime, setCurrentTime] = useState<string>('--:--');
  const [expanded, setExpanded] = useState(false);

  /* Resizing Logic */
  useEffect(() => {
    const resizeWindow = async () => {
      const appWindow = getCurrentWindow();
      if (expanded) {
        await appWindow.setSize(new LogicalSize(310, 500));
      } else {
        await appWindow.setSize(new LogicalSize(310, 270));
      }
    };
    resizeWindow();
  }, [expanded]);
  const [completedPrayers, setCompletedPrayers] = useState<Set<string>>(new Set());
  const [showMenu, setShowMenu] = useState(false);
  const [isAddingLocation, setIsAddingLocation] = useState(false);
  const [newCityInput, setNewCityInput] = useState("");
  const dataRef = useRef<{ times: PrayerTimes | null }>({ times: null });

  // Initial Load
  useEffect(() => {
    initApp();

    // Timer for clock and countdown
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const initApp = async () => {
    // 1. Try to load last used or first saved location
    if (savedLocations.length > 0) {
      selectLocation(savedLocations[0]);
      return;
    }

    // 2. Auto-detect if no saved locations
    try {
      const loc = await api.getLocationAuto();
      // Auto-save auto-detected location? Maybe just set it for now.
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

  /* Location Management */
  const saveLocations = (locs: LocationData[]) => {
    setSavedLocations(locs);
    localStorage.setItem('savedLocations', JSON.stringify(locs));
  };

  const handleAddLocation = async () => {
    if (!newCityInput.trim()) return;
    try {
      const res = await api.searchCity(newCityInput);

      // 1. Ensure CURRENT location is saved if it exists and isn't in list
      let currentLocs = [...savedLocations];
      if (location && !currentLocs.some(l => l.city === location.city)) {
        currentLocs.push(location);
      }

      // 2. Add NEW location if not duplicate
      if (!currentLocs.some(l => l.city === res.city)) {
        currentLocs.push(res);
      }

      saveLocations(currentLocs);
      selectLocation(res);
      setNewCityInput("");
      setIsAddingLocation(false);
    } catch (e) {
      alert("Location not found");
    }
  };

  const toggleAddingLocation = () => {
    setIsAddingLocation(!isAddingLocation);
    if (!isAddingLocation) {
      setNewCityInput("");
    }
  };

  const selectLocation = async (loc: LocationData) => {
    setLocation(loc);
    // Persist current selection preference if desired, or just session based
    await refreshData(loc.lat, loc.lon);
    setShowMenu(false);
  };

  const removeLocation = (e: React.MouseEvent, city: string) => {
    e.stopPropagation();
    const newLocs = savedLocations.filter(l => l.city !== city);
    saveLocations(newLocs);
    if (location?.city === city && newLocs.length > 0) {
      selectLocation(newLocs[0]);
    } else if (newLocs.length === 0) {
      setLocation(null);
      setPrayerTimes(null);
    }
  };

  const prayerOrder = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];

  return (
    <div className="widget-container">
      {/* Title Bar Drag Region */}
      <div className="widget-header" data-tauri-drag-region></div>

      {/* Header */}
      <div className="header">
        <div className="header-left">
          <div
            className="city-badge"
            onClick={() => setShowMenu(!showMenu)}
          >
            {location?.city.toUpperCase() || "LOADING..."}
          </div>
        </div>
        <div className="clock">{currentTime}</div>
      </div>


      {/* Menu Overlay */}
      {showMenu && (
        <div className="location-menu">
          <div className="location-list">
            {savedLocations.map(loc => (
              <div
                key={loc.city}
                className={`menu-item ${location?.city === loc.city ? 'active' : ''}`}
                onClick={() => selectLocation(loc)}
              >
                <span className="city-name">{loc.city}</span>
                <span className="close-btn" onClick={(e) => removeLocation(e, loc.city)}>×</span>
              </div>
            ))}
          </div>

          {isAddingLocation ? (
            <div className="menu-input-row">
              <input
                autoFocus
                className="menu-input"
                placeholder="Enter city..."
                value={newCityInput}
                onChange={(e) => setNewCityInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddLocation()}
              />
              <button className="menu-btn search-btn" onClick={handleAddLocation}>✓</button>
              <button className="menu-btn cancel-btn" onClick={() => setIsAddingLocation(false)}>✕</button>
            </div>
          ) : (
            <div className="menu-item add-btn" onClick={toggleAddingLocation}>+ Add Location</div>
          )}

          <div className="menu-item quit-btn" onClick={() => api.closeWindow()}>Quit</div>
        </div>
      )}

      {/* Hero */}
      <div className="hero">
        <div className="next-label">{nextPrayer.name.toUpperCase() || "NEXT PRAYER"}</div>
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
