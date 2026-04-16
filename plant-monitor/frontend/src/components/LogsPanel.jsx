import React, { useState, useEffect } from 'react';

const LogsPanel = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const logsEndRef = React.useRef(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchLogs = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/logs/latest?limit=100');
      const data = await response.json();
      
      if (data.success) {
        setLogs(data.lines);
        setLastRefresh(new Date());
        setError(null);
        setTimeout(scrollToBottom, 100);
      } else {
        setError('Failed to fetch logs');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchLogs();
    }, 1000); // Refresh every 1 second

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const formatTime = (date) => {
    if (!date) return '';
    return date.toLocaleTimeString();
  };

  const styles = {
    container: {
      backgroundColor: '#1a1a1a',
      borderRadius: '8px',
      padding: '20px',
      marginTop: '20px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '15px',
      borderBottom: '2px solid #333',
      paddingBottom: '10px',
    },
    title: {
      margin: 0,
      color: '#fff',
      fontSize: '20px',
      fontWeight: 'bold',
    },
    controls: {
      display: 'flex',
      alignItems: 'center',
      gap: '15px',
    },
    refreshInfo: {
      color: '#888',
      fontSize: '12px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    },
    liveIndicator: {
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: '#4CAF50',
      animation: 'pulse 2s infinite',
    },
    toggleButton: {
      padding: '6px 12px',
      backgroundColor: autoRefresh ? '#4CAF50' : '#666',
      color: '#fff',
      border: 'none',
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: '12px',
      transition: 'background-color 0.3s',
    },
    refreshButton: {
      padding: '6px 12px',
      backgroundColor: '#2196F3',
      color: '#fff',
      border: 'none',
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: '12px',
    },
    logsContainer: {
      backgroundColor: '#0d0d0d',
      border: '1px solid #333',
      borderRadius: '4px',
      padding: '15px',
      maxHeight: '500px',
      minHeight: '300px',
      overflowY: 'auto',
      fontFamily: "'Courier New', Courier, monospace",
      fontSize: '14px',
      lineHeight: '1.8',
    },
    logLine: {
      color: '#e0e0e0',
      marginBottom: '6px',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word',
      padding: '2px 0',
    },
    logLineInfo: {
      color: '#4CAF50',
    },
    logLineWarning: {
      color: '#FFC107',
    },
    logLineError: {
      color: '#f44336',
    },
    logLineDebug: {
      color: '#888',
    },
    errorMessage: {
      color: '#f44336',
      padding: '10px',
      backgroundColor: '#2a1515',
      borderRadius: '4px',
      marginTop: '10px',
    },
    loadingMessage: {
      color: '#888',
      textAlign: 'center',
      padding: '20px',
    },
    emptyMessage: {
      color: '#888',
      textAlign: 'center',
      padding: '20px',
      fontStyle: 'italic',
    },
  };

  const getLogLineStyle = (line) => {
    const baseStyle = { ...styles.logLine };
    
    if (line.includes('ERROR')) {
      return { ...baseStyle, ...styles.logLineError };
    } else if (line.includes('WARNING')) {
      return { ...baseStyle, ...styles.logLineWarning };
    } else if (line.includes('DEBUG')) {
      return { ...baseStyle, ...styles.logLineDebug };
    } else if (line.includes('INFO')) {
      return { ...baseStyle, ...styles.logLineInfo };
    }
    
    return baseStyle;
  };

  return (
    <>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
      <div style={styles.container}>
        <div style={styles.header}>
          <h2 style={styles.title}>📋 System Logs</h2>
        <div style={styles.controls}>
          {lastRefresh && (
            <span style={styles.refreshInfo}>
              {autoRefresh && <span style={styles.liveIndicator}></span>}
              {autoRefresh ? 'Live' : 'Paused'} • Last: {formatTime(lastRefresh)}
            </span>
          )}
          <button
            style={styles.toggleButton}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '⏸ Pause' : '▶ Resume'} Auto-refresh
          </button>
          <button
            style={styles.refreshButton}
            onClick={fetchLogs}
            disabled={loading}
          >
            🔄 Refresh Now
          </button>
        </div>
      </div>

      {error && (
        <div style={styles.errorMessage}>
          ⚠️ {error}
        </div>
      )}

      {loading && logs.length === 0 ? (
        <div style={styles.loadingMessage}>
          Loading logs...
        </div>
      ) : logs.length === 0 ? (
        <div style={styles.emptyMessage}>
          No logs available
        </div>
      ) : (
        <div style={styles.logsContainer}>
          {logs.map((line, index) => (
            <div key={index} style={getLogLineStyle(line)}>
              {line}
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      )}
      </div>
    </>
  );
};

export default LogsPanel;
