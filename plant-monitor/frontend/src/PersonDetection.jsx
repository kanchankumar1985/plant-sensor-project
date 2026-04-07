import React, { useState, useEffect } from 'react';

const PersonDetection = () => {
  const [detection, setDetection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLatestDetection = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/snapshots/latest-detection');
      if (!response.ok) {
        throw new Error('Failed to fetch detection data');
      }
      const data = await response.json();
      setDetection(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching detection:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestDetection();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchLatestDetection, 30000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading person detection...</div>
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

  if (!detection) {
    return (
      <div style={styles.container}>
        <h2 style={styles.title}>👤 Person Detection</h2>
        <div style={styles.noData}>No detection data available yet</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>👤 Person Detection</h2>
        <button onClick={fetchLatestDetection} style={styles.refreshButton}>
          🔄 Refresh
        </button>
      </div>

      <div style={styles.card}>
        {/* Boxed Image */}
        <div style={styles.imageContainer}>
          <img 
            src={detection.boxed_image_url || detection.image_url} 
            alt="Person detection" 
            style={styles.image}
            onError={(e) => {
              e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%23ddd" width="400" height="300"/><text x="50%" y="50%" text-anchor="middle" fill="%23999">Image not available</text></svg>';
            }}
          />
        </div>

        {/* Detection Status */}
        <div style={styles.statusSection}>
          <div style={{
            ...styles.statusBadge,
            backgroundColor: detection.person_detected ? '#fef3c7' : '#d1fae5',
            borderColor: detection.person_detected ? '#f59e0b' : '#10b981',
          }}>
            <span style={{
              ...styles.statusIcon,
              color: detection.person_detected ? '#f59e0b' : '#10b981',
            }}>
              {detection.person_detected ? '⚠️' : '✅'}
            </span>
            <span style={{
              ...styles.statusText,
              color: detection.person_detected ? '#92400e' : '#065f46',
            }}>
              {detection.person_detected 
                ? `Person Detected (${detection.person_count})` 
                : 'No Person Detected'}
            </span>
          </div>
        </div>

        {/* Metadata */}
        <div style={styles.metadata}>
          <div style={styles.metadataRow}>
            <span style={styles.label}>📅 Captured:</span>
            <span style={styles.value}>
              {new Date(detection.time).toLocaleString()}
            </span>
          </div>

          <div style={styles.metadataRow}>
            <span style={styles.label}>🌡️ Temperature:</span>
            <span style={styles.value}>{detection.temperature_c.toFixed(2)}°C</span>
          </div>

          <div style={styles.metadataRow}>
            <span style={styles.label}>💧 Humidity:</span>
            <span style={styles.value}>{detection.humidity_pct.toFixed(2)}%</span>
          </div>

          <div style={styles.metadataRow}>
            <span style={styles.label}>💡 LED Status:</span>
            <span style={{
              ...styles.value,
              color: detection.led_state ? '#22c55e' : '#ef4444',
              fontWeight: 'bold'
            }}>
              {detection.led_state ? 'ON' : 'OFF'}
            </span>
          </div>

          <div style={styles.metadataRow}>
            <span style={styles.label}>👥 Person Count:</span>
            <span style={styles.value}>{detection.person_count}</span>
          </div>
        </div>

        {/* Detection Details */}
        {detection.detection_metadata && detection.detection_metadata.detections && 
         detection.detection_metadata.detections.length > 0 && (
          <div style={styles.detailsSection}>
            <h3 style={styles.detailsTitle}>🔍 Detection Details</h3>
            {detection.detection_metadata.detections.map((det, idx) => (
              <div key={idx} style={styles.detectionItem}>
                <div style={styles.detectionHeader}>
                  <span style={styles.detectionClass}>Person #{idx + 1}</span>
                  <span style={styles.detectionConfidence}>
                    {(det.confidence * 100).toFixed(1)}% confidence
                  </span>
                </div>
                <div style={styles.bboxInfo}>
                  <span style={styles.bboxLabel}>Bounding Box:</span>
                  <span style={styles.bboxValue}>
                    [{det.bbox_xyxy.map(v => Math.round(v)).join(', ')}]
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Raw JSON Metadata */}
        <div style={styles.jsonSection}>
          <h3 style={styles.jsonTitle}>📋 Raw Detection Metadata</h3>
          <pre style={styles.jsonPre}>
            {JSON.stringify(detection.detection_metadata, null, 2)}
          </pre>
        </div>

        {/* VLM Result */}
        {detection.vlm_result && (
          <div style={styles.vlmSection}>
            <span style={styles.label}>🤖 Plant Analysis:</span>
            <p style={styles.vlmText}>{detection.vlm_result}</p>
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '1000px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
  },
  refreshButton: {
    padding: '10px 20px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
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
  statusSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  statusBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    borderRadius: '8px',
    border: '2px solid',
  },
  statusIcon: {
    fontSize: '24px',
  },
  statusText: {
    fontSize: '18px',
    fontWeight: '600',
  },
  metadata: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  metadataRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px 0',
    borderBottom: '1px solid #f3f4f6',
  },
  label: {
    fontWeight: '600',
    color: '#6b7280',
  },
  value: {
    color: '#1f2937',
    fontWeight: '500',
  },
  detailsSection: {
    padding: '20px',
    backgroundColor: '#f9fafb',
    borderBottom: '1px solid #e5e7eb',
  },
  detailsTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '16px',
  },
  detectionItem: {
    backgroundColor: 'white',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '12px',
    border: '1px solid #e5e7eb',
  },
  detectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px',
  },
  detectionClass: {
    fontWeight: '600',
    color: '#1f2937',
  },
  detectionConfidence: {
    fontSize: '14px',
    color: '#10b981',
    fontWeight: '600',
  },
  bboxInfo: {
    display: 'flex',
    gap: '8px',
    fontSize: '13px',
  },
  bboxLabel: {
    color: '#6b7280',
  },
  bboxValue: {
    color: '#1f2937',
    fontFamily: 'monospace',
  },
  jsonSection: {
    padding: '20px',
    backgroundColor: '#f9fafb',
  },
  jsonTitle: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '12px',
  },
  jsonPre: {
    backgroundColor: '#1f2937',
    color: '#10b981',
    padding: '16px',
    borderRadius: '8px',
    overflow: 'auto',
    fontSize: '13px',
    fontFamily: 'monospace',
    margin: 0,
  },
  vlmSection: {
    padding: '20px',
    backgroundColor: '#f0f9ff',
    borderTop: '1px solid #e5e7eb',
  },
  vlmText: {
    fontSize: '15px',
    color: '#1e40af',
    lineHeight: '1.6',
    margin: '8px 0 0 0',
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

export default PersonDetection;
