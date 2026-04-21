import React, { useState, useEffect } from 'react';

const TouchWorkflowCard = ({ refreshInterval = 2000 }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/touch-workflow/status');
      if (!response.ok) {
        throw new Error('Failed to fetch workflow status');
      }
      const data = await response.json();
      setStatus(data.status);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching workflow status:', err);
    } finally {
      setLoading(false);
    }
  };

  const triggerWorkflow = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/touch-workflow/trigger', {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error('Failed to trigger workflow');
      }
      const data = await response.json();
      setStatus(data.workflow_status);
    } catch (err) {
      setError(err.message);
      console.error('Error triggering workflow:', err);
    }
  };

  const testTTS = async () => {
    try {
      await fetch('http://localhost:8000/api/touch-workflow/test-tts', {
        method: 'POST'
      });
    } catch (err) {
      console.error('Error testing TTS:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStatusColor = (status) => {
    const colors = {
      idle: '#6b7280',
      triggered: '#f59e0b',
      running: '#3b82f6',
      completed: '#10b981',
      failed: '#ef4444'
    };
    return colors[status] || '#6b7280';
  };

  const getStatusIcon = (status) => {
    const icons = {
      idle: '⏸️',
      triggered: '⚡',
      running: '⚙️',
      completed: '✅',
      failed: '❌'
    };
    return icons[status] || '❓';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleString();
  };

  if (loading && !status) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading workflow status...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>🖐️ Touch Workflow</h2>
        <div style={styles.controls}>
          <button onClick={testTTS} style={styles.testButton}>
            🔊 Test TTS
          </button>
          <button onClick={triggerWorkflow} style={styles.triggerButton}>
            ⚡ Trigger Workflow
          </button>
          <button onClick={fetchStatus} style={styles.refreshButton}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && (
        <div style={styles.error}>
          ⚠️ {error}
        </div>
      )}

      {status && (
        <div style={styles.card}>
          {/* Status Badge */}
          <div style={styles.statusSection}>
            <div style={{
              ...styles.statusBadge,
              backgroundColor: getStatusColor(status.status) + '20',
              borderColor: getStatusColor(status.status),
            }}>
              <span style={styles.statusIcon}>
                {getStatusIcon(status.status)}
              </span>
              <span style={{
                ...styles.statusText,
                color: getStatusColor(status.status)
              }}>
                {status.status?.toUpperCase() || 'UNKNOWN'}
              </span>
            </div>
          </div>

          {/* Last Trigger Time */}
          <div style={styles.infoSection}>
            <div style={styles.infoRow}>
              <span style={styles.label}>⏰ Last Trigger:</span>
              <span style={styles.value}>
                {formatTimestamp(status.last_trigger_time)}
              </span>
            </div>

            {status.current_step && (
              <div style={styles.infoRow}>
                <span style={styles.label}>📍 Current Step:</span>
                <span style={styles.value}>
                  {status.current_step.replace(/_/g, ' ').toUpperCase()}
                </span>
              </div>
            )}

            {status.last_message && (
              <div style={styles.infoRow}>
                <span style={styles.label}>💬 Last Message:</span>
                <span style={styles.value}>"{status.last_message}"</span>
              </div>
            )}
          </div>

          {/* Workflow Progress */}
          {status.status === 'running' && (
            <div style={styles.progressSection}>
              <h3 style={styles.sectionTitle}>⚙️ Workflow Progress</h3>
              <div style={styles.progressSteps}>
                <div style={styles.progressStep}>
                  <div style={styles.stepIndicator}>
                    {status.image_path ? '✓' : '○'}
                  </div>
                  <span style={styles.stepLabel}>Capture Snapshot</span>
                </div>
                <div style={styles.progressStep}>
                  <div style={styles.stepIndicator}>
                    {status.video_path ? '✓' : '○'}
                  </div>
                  <span style={styles.stepLabel}>Record Video</span>
                </div>
                <div style={styles.progressStep}>
                  <div style={styles.stepIndicator}>
                    {status.yolo_result ? '✓' : '○'}
                  </div>
                  <span style={styles.stepLabel}>YOLO Detection</span>
                </div>
                <div style={styles.progressStep}>
                  <div style={styles.stepIndicator}>○</div>
                  <span style={styles.stepLabel}>VLM Analysis</span>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          {status.status === 'completed' && (
            <div style={styles.resultsSection}>
              <h3 style={styles.sectionTitle}>📊 Results</h3>
              
              {status.image_path && (
                <div style={styles.resultItem}>
                  <span style={styles.resultIcon}>📸</span>
                  <span style={styles.resultLabel}>Image:</span>
                  <span style={styles.resultValue}>
                    {status.image_path.split('/').pop()}
                  </span>
                </div>
              )}

              {status.video_path && (
                <div style={styles.resultItem}>
                  <span style={styles.resultIcon}>🎥</span>
                  <span style={styles.resultLabel}>Video:</span>
                  <span style={styles.resultValue}>
                    {status.video_path.split('/').pop()}
                  </span>
                </div>
              )}

              {status.yolo_result && (
                <div style={styles.resultItem}>
                  <span style={styles.resultIcon}>👤</span>
                  <span style={styles.resultLabel}>Person Detected:</span>
                  <span style={styles.resultValue}>
                    {status.yolo_result.person_detected ? 'Yes' : 'No'}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Error */}
          {status.error && (
            <div style={styles.errorSection}>
              <h3 style={styles.sectionTitle}>❌ Error</h3>
              <p style={styles.errorText}>{status.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '800px',
    margin: '20px auto',
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
  controls: {
    display: 'flex',
    gap: '10px',
  },
  testButton: {
    padding: '8px 16px',
    backgroundColor: '#8b5cf6',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  triggerButton: {
    padding: '8px 16px',
    backgroundColor: '#f59e0b',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  refreshButton: {
    padding: '8px 16px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
  },
  statusSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'center',
  },
  statusBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 24px',
    borderRadius: '24px',
    border: '2px solid',
  },
  statusIcon: {
    fontSize: '24px',
  },
  statusText: {
    fontSize: '18px',
    fontWeight: 'bold',
  },
  infoSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  infoRow: {
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
  progressSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#f0f9ff',
  },
  sectionTitle: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '16px',
  },
  progressSteps: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  progressStep: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  stepIndicator: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: '#e5e7eb',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '16px',
    fontWeight: 'bold',
  },
  stepLabel: {
    fontSize: '14px',
    color: '#4b5563',
  },
  resultsSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  resultItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '8px 0',
  },
  resultIcon: {
    fontSize: '20px',
  },
  resultLabel: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#6b7280',
  },
  resultValue: {
    fontSize: '14px',
    color: '#1f2937',
  },
  errorSection: {
    padding: '20px',
    backgroundColor: '#fef2f2',
  },
  errorText: {
    fontSize: '14px',
    color: '#991b1b',
    margin: 0,
  },
  loading: {
    textAlign: 'center',
    padding: '40px',
    color: '#6b7280',
    fontSize: '18px',
  },
  error: {
    padding: '16px',
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '8px',
    color: '#991b1b',
    marginBottom: '20px',
  },
};

export default TouchWorkflowCard;
