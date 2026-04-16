import React, { useState, useEffect } from 'react';

const AIStatusCard = ({ refreshInterval = 10000 }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAIStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/analysis/status');
      if (!response.ok) {
        throw new Error('Failed to fetch AI status');
      }
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching AI status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAIStatus();
    const interval = setInterval(fetchAIStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getConnectionStatusColor = (connected) => {
    return connected ? '#10b981' : '#ef4444';
  };

  const getConnectionStatusText = (connected) => {
    return connected ? 'CONNECTED' : 'DISCONNECTED';
  };

  const getProcessingStatusColor = (count) => {
    if (count === 0) return '#10b981';
    if (count < 5) return '#f59e0b';
    return '#ef4444';
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading AI status...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <h2 style={styles.title}>🤖 AI System Status</h2>
        <div style={styles.card}>
          <div style={styles.errorSection}>
            <div style={styles.errorIcon}>⚠️</div>
            <div style={styles.errorContent}>
              <h3 style={styles.errorTitle}>Connection Error</h3>
              <p style={styles.errorText}>{error}</p>
              <button onClick={fetchAIStatus} style={styles.retryButton}>
                🔄 Retry Connection
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div style={styles.container}>
        <h2 style={styles.title}>🤖 AI System Status</h2>
        <div style={styles.noData}>No status data available</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>🤖 AI System Status</h2>
        <button onClick={fetchAIStatus} style={styles.refreshButton}>
          🔄 Refresh
        </button>
      </div>

      <div style={styles.card}>
        {/* Ollama Connection Status */}
        <div style={styles.connectionSection}>
          <h3 style={styles.sectionTitle}>🔌 Ollama Connection</h3>
          
          <div style={styles.connectionStatus}>
            <div style={{
              ...styles.statusIndicator,
              backgroundColor: getConnectionStatusColor(status.ollama_connected)
            }} />
            <div style={styles.connectionInfo}>
              <span style={{
                ...styles.connectionText,
                color: getConnectionStatusColor(status.ollama_connected)
              }}>
                {getConnectionStatusText(status.ollama_connected)}
              </span>
              {status.ollama_host && (
                <span style={styles.connectionHost}>
                  {status.ollama_host}
                </span>
              )}
            </div>
          </div>

          {!status.ollama_connected && (
            <div style={styles.connectionHelp}>
              <p style={styles.helpText}>
                ⚠️ Ollama is not running. Start it with:
              </p>
              <code style={styles.codeBlock}>ollama serve</code>
            </div>
          )}
        </div>

        {/* Model Information */}
        <div style={styles.modelSection}>
          <h3 style={styles.sectionTitle}>🧠 Model Information</h3>
          
          <div style={styles.modelGrid}>
            <div style={styles.modelItem}>
              <span style={styles.modelLabel}>Model Name</span>
              <span style={styles.modelValue}>
                {status.model_name || 'N/A'}
              </span>
            </div>
            
            <div style={styles.modelItem}>
              <span style={styles.modelLabel}>Model Size</span>
              <span style={styles.modelValue}>
                {status.model_size || 'Unknown'}
              </span>
            </div>
            
            <div style={styles.modelItem}>
              <span style={styles.modelLabel}>Available Models</span>
              <span style={styles.modelValue}>
                {status.available_models?.length || 0}
              </span>
            </div>
            
            <div style={styles.modelItem}>
              <span style={styles.modelLabel}>Last Updated</span>
              <span style={styles.modelValue}>
                {status.model_updated_at 
                  ? new Date(status.model_updated_at).toLocaleDateString()
                  : 'Unknown'}
              </span>
            </div>
          </div>

          {status.available_models && status.available_models.length > 0 && (
            <div style={styles.modelsList}>
              <span style={styles.modelsListLabel}>Available Models:</span>
              <div style={styles.modelsListItems}>
                {status.available_models.map((model, idx) => (
                  <span 
                    key={idx} 
                    style={{
                      ...styles.modelTag,
                      backgroundColor: model === status.model_name ? '#dbeafe' : '#f3f4f6',
                      borderColor: model === status.model_name ? '#3b82f6' : '#d1d5db',
                      color: model === status.model_name ? '#1e40af' : '#4b5563'
                    }}
                  >
                    {model === status.model_name && '✓ '}
                    {model}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Processing Queue */}
        <div style={styles.queueSection}>
          <h3 style={styles.sectionTitle}>📋 Processing Queue</h3>
          
          <div style={styles.queueStats}>
            <div style={styles.queueStat}>
              <div style={styles.queueStatIcon}>⏳</div>
              <div style={styles.queueStatInfo}>
                <span style={styles.queueStatLabel}>Pending</span>
                <span style={{
                  ...styles.queueStatValue,
                  color: getProcessingStatusColor(status.pending_count || 0)
                }}>
                  {status.pending_count || 0}
                </span>
              </div>
            </div>

            <div style={styles.queueStat}>
              <div style={styles.queueStatIcon}>⚙️</div>
              <div style={styles.queueStatInfo}>
                <span style={styles.queueStatLabel}>Processing</span>
                <span style={{
                  ...styles.queueStatValue,
                  color: status.processing_count > 0 ? '#f59e0b' : '#10b981'
                }}>
                  {status.processing_count || 0}
                </span>
              </div>
            </div>

            <div style={styles.queueStat}>
              <div style={styles.queueStatIcon}>✅</div>
              <div style={styles.queueStatInfo}>
                <span style={styles.queueStatLabel}>Completed</span>
                <span style={styles.queueStatValue}>
                  {status.completed_count || 0}
                </span>
              </div>
            </div>

            <div style={styles.queueStat}>
              <div style={styles.queueStatIcon}>❌</div>
              <div style={styles.queueStatInfo}>
                <span style={styles.queueStatLabel}>Failed</span>
                <span style={{
                  ...styles.queueStatValue,
                  color: status.failed_count > 0 ? '#ef4444' : '#6b7280'
                }}>
                  {status.failed_count || 0}
                </span>
              </div>
            </div>
          </div>

          {status.current_task && (
            <div style={styles.currentTask}>
              <span style={styles.currentTaskLabel}>Current Task:</span>
              <span style={styles.currentTaskValue}>{status.current_task}</span>
            </div>
          )}
        </div>

        {/* Recent Analysis */}
        <div style={styles.recentSection}>
          <h3 style={styles.sectionTitle}>📊 Recent Analysis</h3>
          
          <div style={styles.recentStats}>
            <div style={styles.recentStat}>
              <span style={styles.recentStatLabel}>Last Analysis</span>
              <span style={styles.recentStatValue}>
                {status.last_analysis_time 
                  ? new Date(status.last_analysis_time).toLocaleString()
                  : 'Never'}
              </span>
            </div>

            <div style={styles.recentStat}>
              <span style={styles.recentStatLabel}>Analyses Today</span>
              <span style={styles.recentStatValue}>
                {status.analyses_today || 0}
              </span>
            </div>

            <div style={styles.recentStat}>
              <span style={styles.recentStatLabel}>Success Rate</span>
              <span style={styles.recentStatValue}>
                {status.success_rate 
                  ? `${(status.success_rate * 100).toFixed(1)}%`
                  : 'N/A'}
              </span>
            </div>

            <div style={styles.recentStat}>
              <span style={styles.recentStatLabel}>Avg. Processing Time</span>
              <span style={styles.recentStatValue}>
                {status.avg_processing_time 
                  ? `${status.avg_processing_time.toFixed(1)}s`
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Error Log */}
        {status.recent_errors && status.recent_errors.length > 0 && (
          <div style={styles.errorLogSection}>
            <h3 style={styles.sectionTitle}>🚨 Recent Errors</h3>
            
            <div style={styles.errorLogList}>
              {status.recent_errors.slice(0, 5).map((err, idx) => (
                <div key={idx} style={styles.errorLogItem}>
                  <div style={styles.errorLogHeader}>
                    <span style={styles.errorLogTime}>
                      {new Date(err.time).toLocaleString()}
                    </span>
                    <span style={styles.errorLogType}>{err.type || 'Error'}</span>
                  </div>
                  <p style={styles.errorLogMessage}>{err.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* System Health */}
        <div style={styles.healthSection}>
          <h3 style={styles.sectionTitle}>💚 System Health</h3>
          
          <div style={styles.healthGrid}>
            <div style={styles.healthItem}>
              <div style={{
                ...styles.healthIndicator,
                backgroundColor: status.ollama_connected ? '#10b981' : '#ef4444'
              }}>
                {status.ollama_connected ? '✓' : '✗'}
              </div>
              <span style={styles.healthLabel}>Ollama Service</span>
            </div>

            <div style={styles.healthItem}>
              <div style={{
                ...styles.healthIndicator,
                backgroundColor: status.database_connected ? '#10b981' : '#ef4444'
              }}>
                {status.database_connected ? '✓' : '✗'}
              </div>
              <span style={styles.healthLabel}>Database</span>
            </div>

            <div style={styles.healthItem}>
              <div style={{
                ...styles.healthIndicator,
                backgroundColor: status.model_loaded ? '#10b981' : '#f59e0b'
              }}>
                {status.model_loaded ? '✓' : '⚠'}
              </div>
              <span style={styles.healthLabel}>Model Loaded</span>
            </div>

            <div style={styles.healthItem}>
              <div style={{
                ...styles.healthIndicator,
                backgroundColor: status.processing_count === 0 ? '#10b981' : '#f59e0b'
              }}>
                {status.processing_count === 0 ? '✓' : '⚙'}
              </div>
              <span style={styles.healthLabel}>Queue Status</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '1200px',
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
  connectionSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  sectionTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '16px',
  },
  connectionStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  statusIndicator: {
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  connectionInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  connectionText: {
    fontSize: '16px',
    fontWeight: 'bold',
  },
  connectionHost: {
    fontSize: '12px',
    color: '#6b7280',
  },
  connectionHelp: {
    marginTop: '12px',
    padding: '12px',
    backgroundColor: '#fef3c7',
    borderRadius: '6px',
    borderLeft: '4px solid #f59e0b',
  },
  helpText: {
    fontSize: '14px',
    color: '#92400e',
    margin: '0 0 8px 0',
  },
  codeBlock: {
    display: 'block',
    padding: '8px 12px',
    backgroundColor: '#1f2937',
    color: '#10b981',
    borderRadius: '4px',
    fontSize: '13px',
    fontFamily: 'monospace',
  },
  modelSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  modelGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '16px',
  },
  modelItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  modelLabel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
  },
  modelValue: {
    fontSize: '16px',
    color: '#1f2937',
    fontWeight: '500',
  },
  modelsList: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '6px',
  },
  modelsListLabel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
    display: 'block',
    marginBottom: '8px',
  },
  modelsListItems: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  modelTag: {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '500',
    border: '1px solid',
  },
  queueSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  queueStats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '16px',
  },
  queueStat: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
  },
  queueStatIcon: {
    fontSize: '32px',
  },
  queueStatInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  queueStatLabel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
  },
  queueStatValue: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#1f2937',
  },
  currentTask: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#dbeafe',
    borderRadius: '6px',
    borderLeft: '4px solid #3b82f6',
  },
  currentTaskLabel: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#1e40af',
    display: 'block',
    marginBottom: '4px',
  },
  currentTaskValue: {
    fontSize: '14px',
    color: '#1e40af',
  },
  recentSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  recentStats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
  },
  recentStat: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  recentStatLabel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
  },
  recentStatValue: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#1f2937',
  },
  errorLogSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#fef2f2',
  },
  errorLogList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  errorLogItem: {
    padding: '12px',
    backgroundColor: 'white',
    borderRadius: '6px',
    border: '1px solid #fecaca',
  },
  errorLogHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px',
  },
  errorLogTime: {
    fontSize: '11px',
    color: '#991b1b',
    fontWeight: '600',
  },
  errorLogType: {
    fontSize: '11px',
    color: '#dc2626',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  errorLogMessage: {
    fontSize: '13px',
    color: '#7f1d1d',
    margin: 0,
    lineHeight: '1.4',
  },
  healthSection: {
    padding: '20px',
  },
  healthGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '16px',
  },
  healthItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  healthIndicator: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
    fontWeight: 'bold',
    color: 'white',
    flexShrink: 0,
  },
  healthLabel: {
    fontSize: '14px',
    color: '#4b5563',
    fontWeight: '500',
  },
  errorSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
    padding: '40px',
  },
  errorIcon: {
    fontSize: '64px',
  },
  errorContent: {
    flex: 1,
  },
  errorTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#dc2626',
    marginTop: 0,
    marginBottom: '8px',
  },
  errorText: {
    fontSize: '14px',
    color: '#991b1b',
    marginBottom: '16px',
  },
  retryButton: {
    padding: '10px 20px',
    backgroundColor: '#dc2626',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  loading: {
    textAlign: 'center',
    padding: '40px',
    color: '#6b7280',
    fontSize: '18px',
  },
  noData: {
    textAlign: 'center',
    padding: '40px',
    color: '#6b7280',
    fontSize: '18px',
  },
};

export default AIStatusCard;
