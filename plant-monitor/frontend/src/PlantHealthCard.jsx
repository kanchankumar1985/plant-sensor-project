import React, { useState, useEffect } from 'react';

const PlantHealthCard = ({ refreshInterval = 60000 }) => {
  const [healthAlerts, setHealthAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealthAlerts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/analysis/health-alerts');
      if (!response.ok) {
        throw new Error('Failed to fetch health alerts');
      }
      const data = await response.json();
      setHealthAlerts(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching health alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthAlerts();
    const interval = setInterval(fetchHealthAlerts, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getHealthStatusColor = (health) => {
    if (health === 'healthy') return { bg: '#d1fae5', border: '#10b981', text: '#065f46' };
    if (health === 'yellowing') return { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' };
    if (health === 'drooping') return { bg: '#fee2e2', border: '#f97316', text: '#991b1b' };
    if (health === 'wilting') return { bg: '#fecaca', border: '#dc2626', text: '#7f1d1d' };
    return { bg: '#f3f4f6', border: '#9ca3af', text: '#4b5563' };
  };

  const getHealthIcon = (health) => {
    if (health === 'healthy') return '🌿';
    if (health === 'yellowing') return '🟡';
    if (health === 'drooping') return '⬇️';
    if (health === 'wilting') return '🥀';
    return '❓';
  };

  const getSeverityLevel = (alert) => {
    if (alert.wilting_visible) return { level: 'CRITICAL', color: '#dc2626', icon: '🚨' };
    if (alert.drooping_visible) return { level: 'HIGH', color: '#f97316', icon: '⚠️' };
    if (alert.yellowing_visible) return { level: 'MEDIUM', color: '#f59e0b', icon: '⚡' };
    return { level: 'LOW', color: '#10b981', icon: 'ℹ️' };
  };

  const getRecommendations = (alert) => {
    const recommendations = [];
    
    if (alert.wilting_visible) {
      recommendations.push('🚨 URGENT: Water plant immediately');
      recommendations.push('Check soil moisture level');
      recommendations.push('Ensure proper drainage');
    }
    
    if (alert.drooping_visible) {
      recommendations.push('💧 Plant may need water');
      recommendations.push('Check if soil is dry');
      recommendations.push('Verify light exposure is adequate');
    }
    
    if (alert.yellowing_visible) {
      recommendations.push('🌞 Check light conditions');
      recommendations.push('Review watering schedule');
      recommendations.push('Consider nutrient deficiency');
    }
    
    if (alert.temperature_c > 28) {
      recommendations.push('🌡️ Temperature is high - ensure adequate ventilation');
    }
    
    if (alert.humidity_pct < 30) {
      recommendations.push('💨 Low humidity - consider misting or humidifier');
    } else if (alert.humidity_pct > 70) {
      recommendations.push('💧 High humidity - check for overwatering');
    }
    
    return recommendations;
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading health alerts...</div>
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

  const latestAlert = healthAlerts[0];

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>🌱 Plant Health Dashboard</h2>
        <button onClick={fetchHealthAlerts} style={styles.refreshButton}>
          🔄 Refresh
        </button>
      </div>

      {/* Current Health Status */}
      {latestAlert && (
        <div style={styles.currentStatusCard}>
          <h3 style={styles.sectionTitle}>Current Health Status</h3>
          
          <div style={styles.statusContainer}>
            <div style={styles.statusIcon}>
              {getHealthIcon(latestAlert.plant_health_guess)}
            </div>
            
            <div style={styles.statusInfo}>
              <div style={{
                ...styles.statusBadge,
                ...getHealthStatusColor(latestAlert.plant_health_guess)
              }}>
                {latestAlert.plant_health_guess?.toUpperCase() || 'UNKNOWN'}
              </div>
              
              <p style={styles.statusSummary}>
                {latestAlert.vlm_summary || 'No summary available'}
              </p>
              
              <div style={styles.statusMetrics}>
                <div style={styles.metric}>
                  <span style={styles.metricIcon}>🌡️</span>
                  <span style={styles.metricValue}>{latestAlert.temperature_c?.toFixed(1)}°C</span>
                </div>
                <div style={styles.metric}>
                  <span style={styles.metricIcon}>💧</span>
                  <span style={styles.metricValue}>{latestAlert.humidity_pct?.toFixed(1)}%</span>
                </div>
                <div style={styles.metric}>
                  <span style={styles.metricIcon}>📅</span>
                  <span style={styles.metricValue}>
                    {new Date(latestAlert.time).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Health Indicators */}
          <div style={styles.indicatorsGrid}>
            <div style={{
              ...styles.indicator,
              borderColor: latestAlert.yellowing_visible ? '#f59e0b' : '#10b981'
            }}>
              <span style={styles.indicatorIcon}>
                {latestAlert.yellowing_visible ? '🟡' : '✅'}
              </span>
              <span style={styles.indicatorLabel}>Yellowing</span>
              <span style={{
                ...styles.indicatorStatus,
                color: latestAlert.yellowing_visible ? '#f59e0b' : '#10b981'
              }}>
                {latestAlert.yellowing_visible ? 'DETECTED' : 'NONE'}
              </span>
            </div>

            <div style={{
              ...styles.indicator,
              borderColor: latestAlert.drooping_visible ? '#f97316' : '#10b981'
            }}>
              <span style={styles.indicatorIcon}>
                {latestAlert.drooping_visible ? '⬇️' : '✅'}
              </span>
              <span style={styles.indicatorLabel}>Drooping</span>
              <span style={{
                ...styles.indicatorStatus,
                color: latestAlert.drooping_visible ? '#f97316' : '#10b981'
              }}>
                {latestAlert.drooping_visible ? 'DETECTED' : 'NONE'}
              </span>
            </div>

            <div style={{
              ...styles.indicator,
              borderColor: latestAlert.wilting_visible ? '#dc2626' : '#10b981'
            }}>
              <span style={styles.indicatorIcon}>
                {latestAlert.wilting_visible ? '🥀' : '✅'}
              </span>
              <span style={styles.indicatorLabel}>Wilting</span>
              <span style={{
                ...styles.indicatorStatus,
                color: latestAlert.wilting_visible ? '#dc2626' : '#10b981'
              }}>
                {latestAlert.wilting_visible ? 'DETECTED' : 'NONE'}
              </span>
            </div>
          </div>

          {/* Actionable Recommendations */}
          <div style={styles.recommendationsSection}>
            <h4 style={styles.recommendationsTitle}>💡 Actionable Recommendations</h4>
            <ul style={styles.recommendationsList}>
              {getRecommendations(latestAlert).map((rec, idx) => (
                <li key={idx} style={styles.recommendationItem}>
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Alert History */}
      {healthAlerts.length > 0 && (
        <div style={styles.historyCard}>
          <h3 style={styles.sectionTitle}>📊 Alert History</h3>
          
          <div style={styles.historyList}>
            {healthAlerts.slice(0, 10).map((alert, idx) => {
              const severity = getSeverityLevel(alert);
              const colors = getHealthStatusColor(alert.plant_health_guess);
              
              return (
                <div key={idx} style={styles.historyItem}>
                  <div style={styles.historyHeader}>
                    <div style={styles.historyTime}>
                      📅 {new Date(alert.time).toLocaleString()}
                    </div>
                    <div style={{
                      ...styles.severityBadge,
                      backgroundColor: severity.color + '20',
                      borderColor: severity.color,
                      color: severity.color
                    }}>
                      {severity.icon} {severity.level}
                    </div>
                  </div>
                  
                  <div style={styles.historyContent}>
                    <div style={{
                      ...styles.historyStatus,
                      backgroundColor: colors.bg,
                      borderColor: colors.border,
                      color: colors.text
                    }}>
                      {getHealthIcon(alert.plant_health_guess)} {alert.plant_health_guess?.toUpperCase()}
                    </div>
                    
                    <p style={styles.historySummary}>
                      {alert.vlm_summary}
                    </p>
                    
                    <div style={styles.historyMetrics}>
                      {alert.yellowing_visible && (
                        <span style={styles.historyTag}>🟡 Yellowing</span>
                      )}
                      {alert.drooping_visible && (
                        <span style={styles.historyTag}>⬇️ Drooping</span>
                      )}
                      {alert.wilting_visible && (
                        <span style={styles.historyTag}>🥀 Wilting</span>
                      )}
                      <span style={styles.historyTag}>
                        🌡️ {alert.temperature_c?.toFixed(1)}°C
                      </span>
                      <span style={styles.historyTag}>
                        💧 {alert.humidity_pct?.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Trend Chart Placeholder */}
      <div style={styles.trendCard}>
        <h3 style={styles.sectionTitle}>📈 Health Trends</h3>
        <div style={styles.trendPlaceholder}>
          <p style={styles.trendText}>
            {healthAlerts.length > 0 
              ? `Tracking ${healthAlerts.length} health event${healthAlerts.length > 1 ? 's' : ''}`
              : 'No health events to display'}
          </p>
          {healthAlerts.length > 0 && (
            <div style={styles.trendSummary}>
              <div style={styles.trendStat}>
                <span style={styles.trendStatLabel}>Total Alerts</span>
                <span style={styles.trendStatValue}>{healthAlerts.length}</span>
              </div>
              <div style={styles.trendStat}>
                <span style={styles.trendStatLabel}>Yellowing Events</span>
                <span style={styles.trendStatValue}>
                  {healthAlerts.filter(a => a.yellowing_visible).length}
                </span>
              </div>
              <div style={styles.trendStat}>
                <span style={styles.trendStatLabel}>Drooping Events</span>
                <span style={styles.trendStatValue}>
                  {healthAlerts.filter(a => a.drooping_visible).length}
                </span>
              </div>
              <div style={styles.trendStat}>
                <span style={styles.trendStatLabel}>Wilting Events</span>
                <span style={styles.trendStatValue}>
                  {healthAlerts.filter(a => a.wilting_visible).length}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {healthAlerts.length === 0 && (
        <div style={styles.noAlertsCard}>
          <div style={styles.noAlertsIcon}>🎉</div>
          <h3 style={styles.noAlertsTitle}>No Health Alerts</h3>
          <p style={styles.noAlertsText}>
            Your plant appears to be healthy! Keep up the good care.
          </p>
        </div>
      )}
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
  currentStatusCard: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    padding: '24px',
    marginBottom: '20px',
  },
  sectionTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '16px',
  },
  statusContainer: {
    display: 'flex',
    gap: '20px',
    marginBottom: '20px',
  },
  statusIcon: {
    fontSize: '64px',
    flexShrink: 0,
  },
  statusInfo: {
    flex: 1,
  },
  statusBadge: {
    display: 'inline-block',
    padding: '8px 16px',
    borderRadius: '16px',
    fontSize: '14px',
    fontWeight: 'bold',
    marginBottom: '12px',
    border: '2px solid',
  },
  statusSummary: {
    fontSize: '16px',
    color: '#4b5563',
    lineHeight: '1.6',
    marginBottom: '12px',
  },
  statusMetrics: {
    display: 'flex',
    gap: '16px',
    flexWrap: 'wrap',
  },
  metric: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  metricIcon: {
    fontSize: '16px',
  },
  metricValue: {
    fontSize: '14px',
    color: '#6b7280',
    fontWeight: '500',
  },
  indicatorsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '12px',
    marginBottom: '20px',
  },
  indicator: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '16px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    border: '2px solid',
  },
  indicatorIcon: {
    fontSize: '32px',
    marginBottom: '8px',
  },
  indicatorLabel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
    marginBottom: '4px',
  },
  indicatorStatus: {
    fontSize: '14px',
    fontWeight: 'bold',
  },
  recommendationsSection: {
    backgroundColor: '#f0fdf4',
    padding: '16px',
    borderRadius: '8px',
    borderLeft: '4px solid #10b981',
  },
  recommendationsTitle: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#065f46',
    marginTop: 0,
    marginBottom: '12px',
  },
  recommendationsList: {
    margin: 0,
    paddingLeft: '20px',
  },
  recommendationItem: {
    fontSize: '14px',
    color: '#065f46',
    lineHeight: '1.6',
    marginBottom: '8px',
  },
  historyCard: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    padding: '24px',
    marginBottom: '20px',
  },
  historyList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  historyItem: {
    padding: '16px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
  },
  historyHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  historyTime: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
  },
  severityBadge: {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: 'bold',
    border: '1px solid',
  },
  historyContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  historyStatus: {
    display: 'inline-block',
    padding: '6px 12px',
    borderRadius: '6px',
    fontSize: '12px',
    fontWeight: 'bold',
    border: '1px solid',
    alignSelf: 'flex-start',
  },
  historySummary: {
    fontSize: '14px',
    color: '#4b5563',
    margin: 0,
    lineHeight: '1.5',
  },
  historyMetrics: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  historyTag: {
    padding: '4px 8px',
    backgroundColor: '#e5e7eb',
    borderRadius: '4px',
    fontSize: '11px',
    color: '#4b5563',
    fontWeight: '500',
  },
  trendCard: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    padding: '24px',
    marginBottom: '20px',
  },
  trendPlaceholder: {
    padding: '40px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    border: '2px dashed #d1d5db',
    textAlign: 'center',
  },
  trendText: {
    fontSize: '16px',
    color: '#6b7280',
    margin: '0 0 20px 0',
  },
  trendSummary: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '16px',
  },
  trendStat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
  },
  trendStatLabel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
  },
  trendStatValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#1f2937',
  },
  noAlertsCard: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    padding: '60px 24px',
    textAlign: 'center',
  },
  noAlertsIcon: {
    fontSize: '64px',
    marginBottom: '16px',
  },
  noAlertsTitle: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#10b981',
    marginTop: 0,
    marginBottom: '12px',
  },
  noAlertsText: {
    fontSize: '16px',
    color: '#6b7280',
    margin: 0,
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
};

export default PlantHealthCard;
