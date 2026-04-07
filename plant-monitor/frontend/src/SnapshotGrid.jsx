import React, { useState, useEffect } from 'react';

const SnapshotGrid = () => {
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [videoError, setVideoError] = useState(false);

  const fetchSnapshots = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/snapshots/recent?limit=10000');
      if (!response.ok) {
        throw new Error('Failed to fetch snapshots');
      }
      const data = await response.json();
      setSnapshots(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching snapshots:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSnapshots();
    
    // Auto-refresh every 20 seconds to catch new snapshots
    const interval = setInterval(fetchSnapshots, 20000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading snapshots...</div>
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

  if (snapshots.length === 0) {
    return (
      <div style={styles.container}>
        <h2 style={styles.title}>📸 Plant Snapshot Gallery</h2>
        <div style={styles.noData}>No snapshots available yet</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>📸 Plant Snapshot Gallery</h2>
        <button onClick={fetchSnapshots} style={styles.refreshButton}>
          🔄 Refresh
        </button>
      </div>

      <div style={styles.grid}>
        {snapshots.map((snapshot, index) => (
          <div 
            key={index} 
            style={styles.card}
            onClick={() => setSelectedSnapshot(snapshot)}
          >
            {/* Image */}
            <div style={styles.imageContainer}>
              <div style={{position:'relative', width:'100%', height:'180px'}}>
                <img 
                  src={snapshot.image_url} 
                  alt={`Plant snapshot ${index + 1}`}
                  style={styles.image}
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200"><rect fill="%23ddd" width="300" height="200"/><text x="50%" y="50%" text-anchor="middle" fill="%23999">Image not available</text></svg>';
                  }}
                />
                {/* SVG overlay for bounding boxes in thumbnail */}
                {snapshot.detection_metadata && snapshot.detection_metadata.detections && snapshot.detection_metadata.detections.length > 0 && (
                  <svg
                    style={{position:'absolute', top:0, left:0, width:'100%', height:'100%', pointerEvents:'none'}}
                    viewBox={`0 0 1280 900`} // adjust as needed
                  >
                    {snapshot.detection_metadata.detections.map((det, idx) => {
                      const [x1, y1, x2, y2] = det.bbox_xyxy;
                      return (
                        <g key={idx}>
                          <rect 
                            x={x1/4} y={y1/2.8} 
                            width={(x2-x1)/4} height={(y2-y1)/2.8} 
                            fill="none" 
                            stroke="#f59e0b" 
                            strokeWidth="2"
                            rx="4"
                          />
                          <text x={x1/4+4} y={Math.max(y1/2.8-8,16)} fill="#f59e0b" fontSize="14" fontWeight="bold" stroke="#fff" strokeWidth="1" paintOrder="stroke" >
                            {`Person ${(det.confidence*100).toFixed(1)}%`}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                )}
                
                {/* Video indicator badge */}
                {snapshot.video_url && (
                  <div style={styles.videoBadge}>
                    <span style={styles.videoBadgeIcon}>📹</span>
                    <span style={styles.videoBadgeText}>Video</span>
                  </div>
                )}
              </div>
            </div>

            {/* Metadata */}
            <div style={styles.metadata}>
              <div style={styles.timestamp}>
                📅 {new Date(snapshot.time).toLocaleString()}
              </div>
              
              <div style={styles.stats}>
                <div style={styles.stat}>
                  <span style={styles.statIcon}>🌡️</span>
                  <span style={styles.statValue}>{snapshot.temperature_c.toFixed(1)}°C</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statIcon}>💧</span>
                  <span style={styles.statValue}>{snapshot.humidity_pct.toFixed(1)}%</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statIcon}>💡</span>
                  <span style={{
                    ...styles.statValue,
                    color: snapshot.led_state ? '#22c55e' : '#ef4444',
                    fontWeight: 'bold'
                  }}>
                    {snapshot.led_state ? 'ON' : 'OFF'}
                  </span>
                </div>
              </div>

              {snapshot.vlm_result && snapshot.vlm_result !== 'Not analyzed yet' && (
                <div style={styles.vlmResult}>
                  <span style={styles.vlmIcon}>🤖</span>
                  <span style={styles.vlmText}>
                    {snapshot.vlm_result}
                    {/* Show confidence if analysis was skipped due to person detection */}
                    {snapshot.vlm_result.startsWith('Skipped: Person detected') && snapshot.detection_metadata && snapshot.detection_metadata.detections && snapshot.detection_metadata.detections.length > 0 && (
                      <>
                        <br/>
                        <span style={{color:'#f59e0b', fontWeight:'bold'}}>
                          Confidence: {(snapshot.detection_metadata.detections[0].confidence * 100).toFixed(1)}%
                        </span>
                      </>
                    )}
                  </span>
                </div>
              )}
              
              {/* Video available indicator */}
              {snapshot.video_url && (
                <div style={styles.videoIndicator}>
                  <span style={styles.videoIndicatorIcon}>🎬</span>
                  <span style={styles.videoIndicatorText}>Video clip available - Click to watch</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {selectedSnapshot && (
        <div style={styles.modalOverlay} onClick={() => {
          setSelectedSnapshot(null);
          setVideoError(false);
        }}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <button 
              style={styles.closeButton}
              onClick={() => {
                setSelectedSnapshot(null);
                setVideoError(false);
              }}
            >
              ✕
            </button>

            {/* Video Player in Modal - Replaces Image */}
            {selectedSnapshot.video_url && !videoError ? (
              <div style={styles.modalVideoContainer}>
                <video 
                  controls 
                  autoPlay
                  preload="auto"
                  style={styles.modalVideo}
                  key={selectedSnapshot.video_url}
                  onError={(e) => {
                    console.error('Video failed to load:', selectedSnapshot.video_url);
                    setVideoError(true);
                  }}
                >
                  <source src={selectedSnapshot.video_url} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              </div>
            ) : (
              <div style={styles.modalImageContainer}>
                <div style={{position:'relative', width:'100%', height:'900px'}}>
                  <img 
                    src={selectedSnapshot.image_url} 
                    alt="Plant snapshot detail"
                    style={styles.modalImage}
                  />
                  {/* SVG overlay for bounding boxes in modal */}
                  {selectedSnapshot.detection_metadata && selectedSnapshot.detection_metadata.detections && selectedSnapshot.detection_metadata.detections.length > 0 && (
                    <svg
                      style={{position:'absolute', top:0, left:0, width:'100%', height:'100%', pointerEvents:'none'}}
                      viewBox={`0 0 1280 900`} // adjust as needed
                    >
                      {selectedSnapshot.detection_metadata.detections.map((det, idx) => {
                        const [x1, y1, x2, y2] = det.bbox_xyxy;
                        return (
                          <g key={idx}>
                            <rect 
                              x={x1} y={y1} 
                              width={x2-x1} height={y2-y1} 
                              fill="none" 
                              stroke="#f59e0b" 
                              strokeWidth="4"
                              rx="8"
                            />
                            <text x={x1+8} y={y1+28} fill="#f59e0b" fontSize="32" fontWeight="bold" stroke="#fff" strokeWidth="2" paintOrder="stroke" >
                              {`Person ${(det.confidence*100).toFixed(1)}%`}
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  )}
                </div>
              </div>
            )}

            <div style={styles.modalDetails}>
              <h3 style={styles.modalTitle}>📸 Snapshot Details</h3>
              
              <div style={styles.modalInfoGrid}>
                <div style={styles.modalInfoItem}>
                  <span style={styles.modalLabel}>📅 Captured:</span>
                  <span style={styles.modalValue}>
                    {new Date(selectedSnapshot.time).toLocaleString()}
                  </span>
                </div>

                <div style={styles.modalInfoItem}>
                  <span style={styles.modalLabel}>🌡️ Temperature:</span>
                  <span style={styles.modalValue}>
                    {selectedSnapshot.temperature_c.toFixed(2)}°C
                  </span>
                </div>

                <div style={styles.modalInfoItem}>
                  <span style={styles.modalLabel}>💧 Humidity:</span>
                  <span style={styles.modalValue}>
                    {selectedSnapshot.humidity_pct.toFixed(2)}%
                  </span>
                </div>

                <div style={styles.modalInfoItem}>
                  <span style={styles.modalLabel}>💡 LED Status:</span>
                  <span style={{
                    ...styles.modalValue,
                    color: selectedSnapshot.led_state ? '#22c55e' : '#ef4444',
                    fontWeight: 'bold'
                  }}>
                    {selectedSnapshot.led_state ? 'ON' : 'OFF'}
                  </span>
                </div>
              </div>

              {selectedSnapshot.vlm_result && (
                <div style={styles.modalVlmSection}>
                  <span style={styles.modalLabel}>🤖 AI Analysis:</span>
                  <p style={styles.modalVlmText}>
                    {selectedSnapshot.vlm_result}
                    {/* Show confidence if analysis was skipped due to person detection */}
                    {selectedSnapshot.vlm_result.startsWith('Skipped: Person detected') && selectedSnapshot.detection_metadata && selectedSnapshot.detection_metadata.detections && selectedSnapshot.detection_metadata.detections.length > 0 && (
                      <>
                        <br/>
                        <span style={{color:'#f59e0b', fontWeight:'bold'}}>
                          Confidence: {(selectedSnapshot.detection_metadata.detections[0].confidence * 100).toFixed(1)}%
                        </span>
                      </>
                    )}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
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
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(8, 1fr)',
    gap: '16px',
    maxHeight: '900px',
    overflowY: 'auto',
    paddingRight: '16px',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
    transition: 'transform 0.2s, box-shadow 0.2s',
    cursor: 'pointer',
    width: '100%',
  },
  imageContainer: {
    width: '100%',
    height: '180px',
    backgroundColor: '#f3f4f6',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  metadata: {
    padding: '12px',
  },
  timestamp: {
    fontSize: '10px',
    color: '#6b7280',
    marginBottom: '8px',
    fontWeight: '500',
  },
  stats: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: '8px',
  },
  stat: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  statIcon: {
    fontSize: '14px',
  },
  statValue: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#1f2937',
  },
  vlmResult: {
    marginTop: '8px',
    padding: '6px',
    backgroundColor: '#f0f9ff',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '6px',
  },
  vlmIcon: {
    fontSize: '14px',
  },
  vlmText: {
    fontSize: '11px',
    color: '#1e40af',
    lineHeight: '1.3',
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
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
    padding: '20px',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: '16px',
    maxWidth: '1800px',
    width: '98%',
    maxHeight: '98vh',
    overflow: 'auto',
    position: 'relative',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  closeButton: {
    position: 'absolute',
    top: '16px',
    right: '16px',
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    color: 'white',
    border: 'none',
    fontSize: '24px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
    transition: 'background-color 0.2s',
  },
  modalImageContainer: {
    width: '100%',
    maxHeight: '900px',
    backgroundColor: '#f3f4f6',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  modalImage: {
    width: '100%',
    height: '900px',
    objectFit: 'cover',
  },
  modalDetails: {
    padding: '24px',
  },
  modalTitle: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: '20px',
    marginTop: 0,
  },
  modalInfoGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '20px',
  },
  modalInfoItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  modalLabel: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#6b7280',
  },
  modalValue: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1f2937',
  },
  modalVlmSection: {
    marginTop: '20px',
    padding: '16px',
    backgroundColor: '#f0f9ff',
    borderRadius: '8px',
    borderLeft: '4px solid #3b82f6',
  },
  modalVlmText: {
    fontSize: '15px',
    color: '#1e40af',
    lineHeight: '1.6',
    margin: '8px 0 0 0',
  },
  videoSection: {
    marginBottom: '24px',
    padding: '16px',
    backgroundColor: '#fef3c7',
    borderRadius: '12px',
    borderLeft: '4px solid #f59e0b',
  },
  videoTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#92400e',
    marginTop: 0,
    marginBottom: '12px',
  },
  video: {
    width: '100%',
    maxHeight: '600px',
    borderRadius: '8px',
    backgroundColor: '#000',
  },
  modalVideoContainer: {
    width: '100%',
    maxHeight: '900px',
    backgroundColor: '#000',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalVideo: {
    width: '100%',
    height: '900px',
    objectFit: 'contain',
  },
  videoBadge: {
    position: 'absolute',
    top: '8px',
    right: '8px',
    backgroundColor: 'rgba(220, 38, 38, 0.95)',
    color: 'white',
    padding: '4px 8px',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '11px',
    fontWeight: '600',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
    zIndex: 5,
  },
  videoBadgeIcon: {
    fontSize: '14px',
  },
  videoBadgeText: {
    fontSize: '10px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  videoIndicator: {
    marginTop: '8px',
    padding: '6px 8px',
    backgroundColor: '#fef3c7',
    borderRadius: '6px',
    borderLeft: '2px solid #f59e0b',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  videoIndicatorIcon: {
    fontSize: '14px',
  },
  videoIndicatorText: {
    fontSize: '10px',
    color: '#92400e',
    fontWeight: '600',
  },
};

export default SnapshotGrid;
