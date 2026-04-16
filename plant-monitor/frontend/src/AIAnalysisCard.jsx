import React, { useState, useEffect } from 'react';

const AIAnalysisCard = ({ refreshInterval = 30000 }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLatestAnalysis = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/analysis/latest-image');
      if (!response.ok) {
        throw new Error('Failed to fetch analysis');
      }
      const data = await response.json();
      setAnalysis(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestAnalysis();
    const interval = setInterval(fetchLatestAnalysis, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getHealthColor = (health) => {
    if (!health) return '#9ca3af';
    if (health === 'healthy') return '#10b981';
    if (health === 'yellowing') return '#f59e0b';
    if (health === 'drooping' || health === 'wilting') return '#ef4444';
    return '#9ca3af';
  };

  const getHealthEmoji = (health) => {
    if (!health || health === 'unknown') return '❓';
    if (health === 'healthy') return '🟢';
    if (health === 'yellowing') return '🟡';
    if (health === 'drooping' || health === 'wilting') return '🔴';
    return '⚪';
  };

  const getConfidenceBadge = (confidence) => {
    const colors = {
      high: { bg: '#d1fae5', border: '#10b981', text: '#065f46' },
      medium: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' },
      low: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b' }
    };
    const color = colors[confidence] || colors.low;
    
    return (
      <span style={{
        padding: '4px 12px',
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: '600',
        backgroundColor: color.bg,
        border: `1px solid ${color.border}`,
        color: color.text
      }}>
        {confidence?.toUpperCase() || 'UNKNOWN'} CONFIDENCE
      </span>
    );
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading AI analysis...</div>
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

  if (!analysis) {
    return (
      <div style={styles.container}>
        <h2 style={styles.title}>🤖 AI Analysis</h2>
        <div style={styles.noData}>No analysis available yet</div>
      </div>
    );
  }

  const reliability = analysis.analysis_reliability || {};
  const vlmAnalysis = analysis.vlm_analysis || {};

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>🤖 AI Vision Analysis</h2>
        <button onClick={fetchLatestAnalysis} style={styles.refreshButton}>
          🔄 Refresh
        </button>
      </div>

      <div style={styles.card}>
        {/* Image with YOLO boxes */}
        <div style={styles.imageContainer}>
          <img 
            src={analysis.boxed_image_url || analysis.image_url} 
            alt="AI Analysis" 
            style={styles.image}
            onError={(e) => {
              e.target.src = analysis.image_url;
            }}
          />
          
          {/* Reliability Badge Overlay */}
          <div style={styles.reliabilityOverlay}>
            {getConfidenceBadge(reliability.confidence)}
          </div>
        </div>

        {/* VLM Summary */}
        <div style={styles.summarySection}>
          <h3 style={styles.sectionTitle}>📝 AI Summary</h3>
          <p style={styles.summaryText}>
            {analysis.vlm_summary || 'No summary available'}
          </p>
        </div>

        {/* Health Indicators */}
        <div style={styles.healthSection}>
          <h3 style={styles.sectionTitle}>🌱 Plant Health Indicators</h3>
          
          <div style={styles.healthGrid}>
            {/* Overall Health */}
            <div style={styles.healthItem}>
              <span style={styles.healthEmoji}>
                {getHealthEmoji(analysis.plant_health_guess)}
              </span>
              <div style={styles.healthInfo}>
                <span style={styles.healthLabel}>Overall Health</span>
                <span style={{
                  ...styles.healthValue,
                  color: getHealthColor(analysis.plant_health_guess)
                }}>
                  {analysis.plant_health_guess?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>
            </div>

            {/* Plant Visible */}
            <div style={styles.healthItem}>
              <span style={styles.healthEmoji}>
                {analysis.plant_visible ? '👁️' : '🚫'}
              </span>
              <div style={styles.healthInfo}>
                <span style={styles.healthLabel}>Plant Visible</span>
                <span style={styles.healthValue}>
                  {analysis.plant_visible ? 'YES' : 'NO'}
                </span>
              </div>
            </div>

            {/* Yellowing */}
            <div style={styles.healthItem}>
              <span style={styles.healthEmoji}>
                {analysis.yellowing_visible ? '🟡' : '✅'}
              </span>
              <div style={styles.healthInfo}>
                <span style={styles.healthLabel}>Yellowing</span>
                <span style={{
                  ...styles.healthValue,
                  color: analysis.yellowing_visible ? '#f59e0b' : '#10b981'
                }}>
                  {analysis.yellowing_visible ? 'DETECTED' : 'NONE'}
                </span>
              </div>
            </div>

            {/* Drooping */}
            <div style={styles.healthItem}>
              <span style={styles.healthEmoji}>
                {analysis.drooping_visible ? '⬇️' : '✅'}
              </span>
              <div style={styles.healthInfo}>
                <span style={styles.healthLabel}>Drooping</span>
                <span style={{
                  ...styles.healthValue,
                  color: analysis.drooping_visible ? '#ef4444' : '#10b981'
                }}>
                  {analysis.drooping_visible ? 'DETECTED' : 'NONE'}
                </span>
              </div>
            </div>

            {/* Wilting */}
            <div style={styles.healthItem}>
              <span style={styles.healthEmoji}>
                {analysis.wilting_visible ? '🥀' : '✅'}
              </span>
              <div style={styles.healthInfo}>
                <span style={styles.healthLabel}>Wilting</span>
                <span style={{
                  ...styles.healthValue,
                  color: analysis.wilting_visible ? '#dc2626' : '#10b981'
                }}>
                  {analysis.wilting_visible ? 'DETECTED' : 'NONE'}
                </span>
              </div>
            </div>

            {/* Image Quality */}
            <div style={styles.healthItem}>
              <span style={styles.healthEmoji}>
                {vlmAnalysis.image_quality === 'good' ? '📸' : '⚠️'}
              </span>
              <div style={styles.healthInfo}>
                <span style={styles.healthLabel}>Image Quality</span>
                <span style={styles.healthValue}>
                  {vlmAnalysis.image_quality?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {reliability.recommendations && reliability.recommendations.length > 0 && (
          <div style={styles.recommendationsSection}>
            <h3 style={styles.sectionTitle}>💡 Recommendations</h3>
            <ul style={styles.recommendationsList}>
              {reliability.recommendations.map((rec, idx) => (
                <li key={idx} style={styles.recommendationItem}>
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Warnings */}
        {reliability.warnings && reliability.warnings.length > 0 && (
          <div style={styles.warningsSection}>
            <h3 style={styles.sectionTitle}>⚠️ Warnings</h3>
            <ul style={styles.warningsList}>
              {reliability.warnings.map((warning, idx) => (
                <li key={idx} style={styles.warningItem}>
                  {warning}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Metadata */}
        <div style={styles.metadata}>
          <div style={styles.metadataRow}>
            <span style={styles.label}>📅 Analyzed:</span>
            <span style={styles.value}>
              {analysis.analyzed_at ? new Date(analysis.analyzed_at).toLocaleString() : 'Not analyzed'}
            </span>
          </div>
          <div style={styles.metadataRow}>
            <span style={styles.label}>🤖 Model:</span>
            <span style={styles.value}>{analysis.vlm_model || 'N/A'}</span>
          </div>
          <div style={styles.metadataRow}>
            <span style={styles.label}>📊 Status:</span>
            <span style={{
              ...styles.value,
              color: analysis.analysis_status === 'completed' ? '#10b981' : '#f59e0b',
              fontWeight: 'bold'
            }}>
              {analysis.analysis_status?.toUpperCase() || 'UNKNOWN'}
            </span>
          </div>
          <div style={styles.metadataRow}>
            <span style={styles.label}>🌡️ Temperature:</span>
            <span style={styles.value}>{analysis.temperature_c?.toFixed(1)}°C</span>
          </div>
          <div style={styles.metadataRow}>
            <span style={styles.label}>💧 Humidity:</span>
            <span style={styles.value}>{analysis.humidity_pct?.toFixed(1)}%</span>
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
  imageContainer: {
    position: 'relative',
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
    maxHeight: '600px',
    objectFit: 'contain',
  },
  reliabilityOverlay: {
    position: 'absolute',
    top: '16px',
    right: '16px',
  },
  summarySection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#f0f9ff',
  },
  sectionTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '12px',
  },
  summaryText: {
    fontSize: '16px',
    color: '#1e40af',
    lineHeight: '1.6',
    margin: 0,
  },
  healthSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  healthGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
  },
  healthItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
  },
  healthEmoji: {
    fontSize: '32px',
  },
  healthInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  healthLabel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
  },
  healthValue: {
    fontSize: '14px',
    fontWeight: 'bold',
    color: '#1f2937',
  },
  recommendationsSection: {
    padding: '20px',
    backgroundColor: '#f0fdf4',
    borderBottom: '1px solid #e5e7eb',
  },
  recommendationsList: {
    margin: '0',
    paddingLeft: '20px',
  },
  recommendationItem: {
    fontSize: '14px',
    color: '#065f46',
    lineHeight: '1.6',
    marginBottom: '8px',
  },
  warningsSection: {
    padding: '20px',
    backgroundColor: '#fef3c7',
    borderBottom: '1px solid #e5e7eb',
  },
  warningsList: {
    margin: '0',
    paddingLeft: '20px',
  },
  warningItem: {
    fontSize: '14px',
    color: '#92400e',
    lineHeight: '1.6',
    marginBottom: '8px',
  },
  metadata: {
    padding: '20px',
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

export default AIAnalysisCard;
