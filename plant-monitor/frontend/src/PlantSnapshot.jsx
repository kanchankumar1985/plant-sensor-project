import React, { useState, useEffect } from 'react';

const PlantSnapshot = () => {
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLatestSnapshot = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/snapshots/latest');
      if (!response.ok) {
        throw new Error('Failed to fetch snapshot');
      }
      const data = await response.json();
      setSnapshot(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching snapshot:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestSnapshot();
    
    // Refresh every 60 seconds
    const interval = setInterval(fetchLatestSnapshot, 60000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading latest snapshot...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>Error: {error}</div>
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div style={styles.container}>
        <div style={styles.noData}>No snapshots available yet</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>🌱 Latest Plant Snapshot</h2>
      
      <div style={styles.card}>
        {/* Plant Image */}
        <div style={styles.imageContainer}>
          <img 
            src={snapshot.image_url} 
            alt="Plant snapshot" 
            style={styles.image}
            onError={(e) => {
              e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%23ddd" width="400" height="300"/><text x="50%" y="50%" text-anchor="middle" fill="%23999">Image not available</text></svg>';
            }}
          />
        </div>

        {/* Metadata */}
        <div style={styles.metadata}>
          <div style={styles.metadataRow}>
            <span style={styles.label}>📅 Captured:</span>
            <span style={styles.value}>
              {new Date(snapshot.time).toLocaleString()}
            </span>
          </div>

          <div style={styles.metadataRow}>
            <span style={styles.label}>🌡️ Temperature:</span>
            <span style={styles.value}>{snapshot.temperature_c.toFixed(2)}°C</span>
          </div>

          <div style={styles.metadataRow}>
            <span style={styles.label}>💧 Humidity:</span>
            <span style={styles.value}>{snapshot.humidity_pct.toFixed(2)}%</span>
          </div>

          <div style={styles.metadataRow}>
            <span style={styles.label}>💡 LED Status:</span>
            <span style={{
              ...styles.value,
              color: snapshot.led_state ? '#22c55e' : '#ef4444',
              fontWeight: 'bold'
            }}>
              {snapshot.led_state ? 'ON' : 'OFF'}
            </span>
          </div>

          <div style={styles.metadataRow}>
            <span style={styles.label}>🤖 AI Analysis:</span>
            <span style={styles.value}>
              {snapshot.vlm_result || 'Not analyzed yet'}
            </span>
          </div>
        </div>

        {/* Refresh Button */}
        <button 
          onClick={fetchLatestSnapshot} 
          style={styles.refreshButton}
        >
          🔄 Refresh
        </button>
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '20px',
    color: '#1f2937',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
  },
  imageContainer: {
    width: '100%',
    backgroundColor: '#f3f4f6',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '400px',
  },
  image: {
    width: '100%',
    height: 'auto',
    maxHeight: '500px',
    objectFit: 'contain',
  },
  metadata: {
    padding: '20px',
  },
  metadataRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px 0',
    borderBottom: '1px solid #e5e7eb',
  },
  label: {
    fontWeight: '600',
    color: '#6b7280',
  },
  value: {
    color: '#1f2937',
    fontWeight: '500',
  },
  refreshButton: {
    width: '100%',
    padding: '12px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  loading: {
    textAlign: 'center',
    padding: '40px',
    color: '#6b7280',
    fontSize: '18px',
  },
  error: {
    textAlign: 'center',
    padding: '40px',
    color: '#ef4444',
    fontSize: '18px',
  },
  noData: {
    textAlign: 'center',
    padding: '40px',
    color: '#6b7280',
    fontSize: '18px',
  },
};

export default PlantSnapshot;
