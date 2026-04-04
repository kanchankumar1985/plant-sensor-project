import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const API_BASE = "http://localhost:8000";

export default function App() {
  const [latest, setLatest] = useState(null);
  const [recent, setRecent] = useState([]);
  const [error, setError] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isCustomRange, setIsCustomRange] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [isLiveMode, setIsLiveMode] = useState(true);

  function setQuickRange(preset) {
    const now = new Date();
    let start;
    
    switch (preset) {
      case "last5min":
        start = new Date(now.getTime() - 5 * 60 * 1000);
        break;
      case "last15min":
        start = new Date(now.getTime() - 15 * 60 * 1000);
        break;
      case "last1hour":
        start = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case "today":
        // Start of today in local timezone
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        break;
      default:
        return;
    }
    
    setSelectedPreset(preset);
    setIsLiveMode(false);
    
    // Convert to local datetime-local format (removes timezone offset issues)
    const formatForInput = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    };
    
    setStartDate(formatForInput(start));
    setEndDate(formatForInput(now));
    setIsCustomRange(true);
    
    // Auto-load the data
    setTimeout(() => loadData(), 100);
  }

  async function loadData() {
    try {
      const latestRes = await fetch(`${API_BASE}/api/readings/latest`);
      
      let recentRes;
      if (!isLiveMode && isCustomRange && startDate && endDate) {
        // Load custom date range
        const startISO = new Date(startDate).toISOString();
        const endISO = new Date(endDate).toISOString();
        recentRes = await fetch(`${API_BASE}/api/readings/range?start_time=${startISO}&end_time=${endISO}`);
      } else {
        // Load recent data (default for live mode)
        recentRes = await fetch(`${API_BASE}/api/readings/recent?limit=30`);
      }

      if (!latestRes.ok || !recentRes.ok) {
        throw new Error("Failed to fetch data");
      }

      const latestJson = await latestRes.json();
      const recentJson = await recentRes.json();

      const chartData = recentJson.map((item) => ({
        ...item,
        label: new Date(item.time).toLocaleTimeString(),
      }));

      setLatest(latestJson);
      setRecent(chartData);
      setError("");
    } catch (err) {
      setError(err.message || "Unknown error");
    }
  }

  async function loadCustomRange() {
    if (!startDate || !endDate) {
      setError("Please select both start and end dates");
      return;
    }
    
    // Validate date range
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (start >= end) {
      setError("Start date must be before end date");
      return;
    }
    
    // Check if range is too far in the future
    const now = new Date();
    if (start > now) {
      setError("Start date cannot be in the future");
      return;
    }
    
    setSelectedPreset(null); // Clear preset selection when using custom range
    setIsLiveMode(false);
    setIsCustomRange(true);
    await loadData();
  }

  function resetToLive() {
    setIsLiveMode(true);
    setIsCustomRange(false);
    setSelectedPreset(null);
    setStartDate("");
    setEndDate("");
    loadData();
  }

  useEffect(() => {
    loadData();
    if (isLiveMode) {
      const timer = setInterval(loadData, 3000);
      return () => clearInterval(timer);
    }
  }, [isLiveMode]);

  return (
    <div style={{ fontFamily: "Arial, sans-serif", padding: 24 }}>
      <h1>Plant Monitor Dashboard</h1>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {/* Date Range Filter */}
      <div style={{ 
        background: "#fff", 
        borderRadius: 12, 
        padding: 20, 
        marginBottom: 24, 
        boxShadow: "0 2px 10px rgba(0,0,0,0.08)" 
      }}>
        <h3 style={{ margin: "0 0 20px 0", color: "#333" }}>📊 Data Time Range</h3>
        
        {/* Quick Presets */}
        <div style={{ marginBottom: 20 }}>
          <p style={{ margin: "0 0 12px 0", fontSize: 14, color: "#666", fontWeight: "500" }}>Quick Select:</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button 
              onClick={() => setQuickRange("last5min")} 
              style={selectedPreset === "last5min" ? presetButtonStyleActive : presetButtonStyle}
            >
              Last 5 Minutes
            </button>
            <button 
              onClick={() => setQuickRange("last15min")} 
              style={selectedPreset === "last15min" ? presetButtonStyleActive : presetButtonStyle}
            >
              Last 15 Minutes
            </button>
            <button 
              onClick={() => setQuickRange("last1hour")} 
              style={selectedPreset === "last1hour" ? presetButtonStyleActive : presetButtonStyle}
            >
              Last Hour
            </button>
            <button 
              onClick={() => setQuickRange("today")} 
              style={selectedPreset === "today" ? presetButtonStyleActive : presetButtonStyle}
            >
              Today
            </button>
          </div>
        </div>

        {/* Custom Date Range */}
        <div style={{ borderTop: "1px solid #eee", paddingTop: 20 }}>
          <p style={{ margin: "0 0 12px 0", fontSize: 14, color: "#666", fontWeight: "500" }}>Custom Range:</p>
          <div style={{ display: "flex", gap: 16, alignItems: "end", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <label style={{ display: "block", marginBottom: 6, fontSize: 14, fontWeight: "500", color: "#333" }}>
                📅 From:
              </label>
              <input
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                style={inputStyleImproved}
                max={new Date().toISOString().slice(0, 16)}
              />
            </div>
            <div style={{ flex: 1, minWidth: 200 }}>
              <label style={{ display: "block", marginBottom: 6, fontSize: 14, fontWeight: "500", color: "#333" }}>
                📅 To:
              </label>
              <input
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                style={inputStyleImproved}
                max={new Date().toISOString().slice(0, 16)}
                min={startDate}
              />
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={loadCustomRange} style={buttonStylePrimary} disabled={!startDate || !endDate}>
                📈 Load Data
              </button>
              <button onClick={resetToLive} style={buttonStyleLive}>
                🔴 Live
              </button>
            </div>
          </div>
        </div>

        {/* Status Display */}
        {!isLiveMode && isCustomRange && startDate && endDate && (
          <div style={statusBoxStyle}>
            <span style={{ fontSize: 16 }}>📊</span>
            <div>
              <p style={{ margin: 0, fontSize: 14, fontWeight: "500", color: "#333" }}>
                Viewing Historical Data
              </p>
              <p style={{ margin: 0, fontSize: 13, color: "#666" }}>
                {new Date(startDate).toLocaleString()} → {new Date(endDate).toLocaleString()}
              </p>
            </div>
          </div>
        )}
        
        {isLiveMode && (
          <div style={statusBoxLive}>
            <span style={{ fontSize: 16 }}>🔴</span>
            <div>
              <p style={{ margin: 0, fontSize: 14, fontWeight: "500", color: "#333" }}>
                Live Data Mode
              </p>
              <p style={{ margin: 0, fontSize: 13, color: "#666" }}>
                Auto-refreshing every 3 seconds
              </p>
            </div>
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
        <div style={cardStyle}>
          <h3>Latest Temperature</h3>
          <p style={valueStyle}>
            {latest ? `${latest.temperature_c.toFixed(2)} °C` : "--"}
          </p>
        </div>

        <div style={cardStyle}>
          <h3>Latest Humidity</h3>
          <p style={valueStyle}>
            {latest ? `${latest.humidity_pct.toFixed(2)} %` : "--"}
          </p>
        </div>

        <div style={cardStyle}>
          <h3>Device</h3>
          <p style={valueStyleSmall}>
            {latest ? latest.device_id : "--"}
          </p>
        </div>

        <div style={cardStyle}>
          <h3>Last Update</h3>
          <p style={valueStyleSmall}>
            {latest ? new Date(latest.time).toLocaleString() : "--"}
          </p>
        </div>
      </div>

      <div style={{ width: "100%", height: 420, background: "#fff", padding: 16, borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.08)" }}>
        <h3>Live Readings</h3>
        <ResponsiveContainer width="100%" height="90%">
          <LineChart data={recent}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="temperature_c" name="Temperature (°C)" stroke="#ff6b6b" strokeWidth={2} dot={false} />
            <Line yAxisId="right" type="monotone" dataKey="humidity_pct" name="Humidity (%)" stroke="#4ecdc4" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const cardStyle = {
  background: "#fff",
  borderRadius: 12,
  padding: 16,
  minWidth: 220,
  boxShadow: "0 2px 10px rgba(0,0,0,0.08)",
};

const valueStyle = {
  fontSize: 28,
  fontWeight: "bold",
  margin: 0,
};

const valueStyleSmall = {
  fontSize: 16,
  margin: 0,
  fontWeight: "500",
};

const inputStyleImproved = {
  padding: "12px 16px",
  borderRadius: 8,
  border: "2px solid #e1e5e9",
  fontSize: 14,
  width: "100%",
  boxSizing: "border-box",
  transition: "border-color 0.2s ease",
  fontFamily: "inherit"
};

const presetButtonStyle = {
  padding: "8px 16px",
  backgroundColor: "#f8f9fa",
  color: "#495057",
  border: "2px solid #e9ecef",
  borderRadius: 20,
  cursor: "pointer",
  fontSize: 13,
  fontWeight: "500",
  transition: "all 0.2s ease",
  whiteSpace: "nowrap"
};

const presetButtonStyleActive = {
  padding: "8px 16px",
  backgroundColor: "#007bff",
  color: "white",
  border: "2px solid #007bff",
  borderRadius: 20,
  cursor: "pointer",
  fontSize: 13,
  fontWeight: "600",
  transition: "all 0.2s ease",
  whiteSpace: "nowrap",
  boxShadow: "0 2px 8px rgba(0, 123, 255, 0.3)"
};

const buttonStylePrimary = {
  padding: "12px 20px",
  backgroundColor: "#007bff",
  color: "white",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: 14,
  fontWeight: "600",
  transition: "background-color 0.2s ease",
  display: "flex",
  alignItems: "center",
  gap: 8
};

const buttonStyleLive = {
  padding: "12px 20px",
  backgroundColor: "#dc3545",
  color: "white",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: 14,
  fontWeight: "600",
  transition: "background-color 0.2s ease",
  display: "flex",
  alignItems: "center",
  gap: 8
};

const statusBoxStyle = {
  marginTop: 16,
  padding: 12,
  backgroundColor: "#e3f2fd",
  border: "1px solid #bbdefb",
  borderRadius: 8,
  display: "flex",
  alignItems: "center",
  gap: 12
};

const statusBoxLive = {
  marginTop: 16,
  padding: 12,
  backgroundColor: "#ffebee",
  border: "1px solid #ffcdd2",
  borderRadius: 8,
  display: "flex",
  alignItems: "center",
  gap: 12
};
