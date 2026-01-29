import { useState, useEffect, useRef } from 'react';
import { getCurrentWindow, LogicalSize } from '@tauri-apps/api/window';
import { api, LocationData, PrayerTimes } from './api';
import './App.css';

function App() {
  /* ============================================
     STATE MANAGEMENT
     ============================================ */

  // Location State
  const [location, setLocation] = useState<LocationData | null>(() => {
    const last = localStorage.getItem('lastLocation');
    if (last) return JSON.parse(last);
    const saved = localStorage.getItem('savedLocations');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.length > 0) return parsed[0];
    }
    return null;
  });
  const [savedLocations, setSavedLocations] = useState<LocationData[]>(() => {
    const saved = localStorage.getItem('savedLocations');
    return saved ? JSON.parse(saved) : [];
  });

  // Prayer Data State
  const [prayerTimes, setPrayerTimes] = useState<PrayerTimes | null>(() => {
    const last = localStorage.getItem('lastPrayerTimes');
    const lastDate = localStorage.getItem('lastPrayerDate');
    const today = new Date().toISOString().split('T')[0];
    if (last && lastDate === today) return JSON.parse(last);
    return null;
  });
  const [nextPrayer, setNextPrayer] = useState<{ name: string, time: string, countdown: string }>({
    name: '--',
    time: '--:--',
    countdown: '--'
  });
  const [currentTime, setCurrentTime] = useState<string>(() =>
    new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  );
  const [completedPrayers, setCompletedPrayers] = useState<Set<string>>(() => {
    const saved = localStorage.getItem('completedPrayers');
    const savedDate = localStorage.getItem('lastPrayerDate');
    const today = new Date().toISOString().split('T')[0];
    if (saved && savedDate === today) return new Set(JSON.parse(saved));
    return new Set();
  });

  // UI State
  const [expanded, setExpanded] = useState(false);
  const [isAnimatingContent, setIsAnimatingContent] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [isAddingLocation, setIsAddingLocation] = useState(false);
  const [newCityInput, setNewCityInput] = useState("");

  // Refs
  const dataRef = useRef<{ times: PrayerTimes | null }>({ times: prayerTimes });

  // Persistence for completed prayers
  useEffect(() => {
    localStorage.setItem('completedPrayers', JSON.stringify(Array.from(completedPrayers)));
  }, [completedPrayers]);

  /* ============================================
     WINDOW RESIZE LOGIC
     ============================================ */
  useEffect(() => {
    const handleResize = async () => {
      const appWindow = getCurrentWindow();
      if (expanded) {
        // Expand window first to give room for animation
        await appWindow.setSize(new LogicalSize(330, 500));
        // Trigger CSS animation after a tiny delay so window is ready
        setTimeout(() => setIsAnimatingContent(true), 10);
      } else {
        // Start CSS collapse animation
        setIsAnimatingContent(false);
        // Wait for CSS transition (400ms) before shrinking window
        setTimeout(async () => {
          await appWindow.setSize(new LogicalSize(330, 280));
        }, 400);
      }
    };
    handleResize();
  }, [expanded]);

  /* ============================================
     INITIALIZATION
     ============================================ */
  useEffect(() => {
    initApp();

    // Timer for clock and countdown
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const initApp = async () => {
    // 1. If we already have fresh data from localStorage initialization, just sync the ref and update time
    if (location && prayerTimes) {
      dataRef.current.times = prayerTimes;
      updateTime();
      // We still run a background refresh to ensure correctness, but the UI is already loaded
      refreshData(location.lat, location.lon);
      return;
    }

    // 2. If we have a location but no fresh prayer times
    if (location) {
      await refreshData(location.lat, location.lon);
      return;
    }

    // 3. Fallback: Try to use the first saved location if available
    if (savedLocations.length > 0) {
      selectLocation(savedLocations[0]);
      return;
    }

    // 4. Ultimate Fallback: Auto-detect if absolutely nothing is saved
    try {
      const loc = await api.getLocationAuto();
      setLocation(loc);
      localStorage.setItem('lastLocation', JSON.stringify(loc));
      await refreshData(loc.lat, loc.lon);
    } catch (e) {
      console.error('Failed to auto-detect location:', e);
    }
  };

  /* ============================================
     DATA MANAGEMENT
     ============================================ */
  const refreshData = async (lat: number, lon: number) => {
    try {
      const times = await api.getPrayerTimes(lat, lon);
      setPrayerTimes(times);
      dataRef.current.times = times;

      // Save to localStorage for sub-second startup next time
      localStorage.setItem('lastPrayerTimes', JSON.stringify(times));
      localStorage.setItem('lastPrayerDate', new Date().toISOString().split('T')[0]);

      updateTime();
    } catch (e) {
      console.error('Failed to fetch prayer times:', e);
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
    if (newSet.has(name)) {
      newSet.delete(name);
    } else {
      newSet.add(name);
    }
    setCompletedPrayers(newSet);
  };

  /* ============================================
     LOCATION MANAGEMENT
     ============================================ */
  const saveLocations = (locs: LocationData[]) => {
    setSavedLocations(locs);
    localStorage.setItem('savedLocations', JSON.stringify(locs));
  };

  const selectLocation = async (loc: LocationData) => {
    setLocation(loc);
    localStorage.setItem('lastLocation', JSON.stringify(loc));
    await refreshData(loc.lat, loc.lon);
    setShowMenu(false);
  };

  const handleAddLocation = async () => {
    if (!newCityInput.trim()) return;

    try {
      const res = await api.searchCity(newCityInput);

      // Ensure current location is saved if it exists and isn't in list
      let currentLocs = [...savedLocations];
      if (location && !currentLocs.some(l => l.city === location.city)) {
        currentLocs.push(location);
      }

      // Add new location if not duplicate
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

  /* ============================================
     HELPERS
     ============================================ */
  const prayerOrder = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];

  const getCityDisplayName = (cityName: string) => {
    return cityName.split(',')[0].toUpperCase();
  };

  /* ============================================
     RENDER
     ============================================ */
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
            {location ? getCityDisplayName(location.city) : "LOADING..."}
          </div>
        </div>
        <div className="clock">{currentTime}</div>
      </div>

      {/* Location Menu Overlay */}
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

      {/* Hero Section */}
      <div className="hero">
        <div className="next-label">{nextPrayer.name.toUpperCase() || "NEXT PRAYER"}</div>
        <div className="next-time">{nextPrayer.time}</div>
        <div className="countdown">{nextPrayer.countdown}</div>
      </div>

      {/* Toggle Divider */}
      <div className="divider" onClick={() => setExpanded(!expanded)}></div>

      {/* Prayer List */}
      <div className={`prayer-list-wrapper ${isAnimatingContent ? 'expanded' : ''}`}>
        <div className="prayer-list">
          {prayerTimes && prayerOrder.map(key => {
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
      </div>
    </div>
  );
}

export default App;
