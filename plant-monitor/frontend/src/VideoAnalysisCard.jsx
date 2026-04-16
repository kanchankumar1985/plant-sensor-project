import React, { useState, useEffect } from 'react';

const VideoAnalysisCard = ({ refreshInterval = 30000 }) => {
  const [videoAnalysis, setVideoAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLatestVideoAnalysis = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/analysis/latest-video');
      if (!response.ok) {
        throw new Error('Failed to fetch video analysis');
      }
      const data = await response.json();
      setVideoAnalysis(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching video analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestVideoAnalysis();
    const interval = setInterval(fetchLatestVideoAnalysis, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getEventTypeColor = (eventType) => {
    const colors = {
      person_interaction: '#f59e0b',
      plant_check: '#3b82f6',
      no_activity: '#10b981',
      unknown: '#6b7280'
    };
    return colors[eventType] || colors.unknown;
  };

  const getEventTypeIcon = (eventType) => {
    const icons = {
      person_interaction: '👤',
      plant_check: '🔍',
      no_activity: '✅',
      unknown: '❓'
    };
    return icons[eventType] || icons.unknown;
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading video analysis...</div>
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

  if (!videoAnalysis) {
    return (
      <div style={styles.container}>
        <h2 style={styles.title}>🎬 Video Event Analysis</h2>
        <div style={styles.noData}>No video analysis available yet</div>
      </div>
    );
  }

  const vlmAnalysis = videoAnalysis.vlm_analysis || {};

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>🎬 Video Event Analysis</h2>
        <button onClick={fetchLatestVideoAnalysis} style={styles.refreshButton}>
          🔄 Refresh
        </button>
      </div>

      <div style={styles.card}>
        {/* Video Player */}
        <div style={styles.videoContainer}>
          <video 
            controls 
            autoPlay
            style={styles.video}
            key={videoAnalysis.video_url}
          >
            <source src={videoAnalysis.video_url} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>

        {/* Event Type Badge */}
        <div style={styles.eventTypeSection}>
          <div style={{
            ...styles.eventTypeBadge,
            backgroundColor: getEventTypeColor(videoAnalysis.event_type) + '20',
            borderColor: getEventTypeColor(videoAnalysis.event_type),
          }}>
            <span style={styles.eventTypeIcon}>
              {getEventTypeIcon(videoAnalysis.event_type)}
            </span>
            <span style={{
              ...styles.eventTypeText,
              color: getEventTypeColor(videoAnalysis.event_type)
            }}>
              {videoAnalysis.event_type?.replace('_', ' ').toUpperCase() || 'UNKNOWN EVENT'}
            </span>
          </div>
        </div>

        {/* AI Summary */}
        <div style={styles.summarySection}>
          <h3 style={styles.sectionTitle}>📝 Event Summary</h3>
          <p style={styles.summaryText}>
            {videoAnalysis.vlm_summary || vlmAnalysis.summary || 'No summary available'}
          </p>
        </div>

        {/* Event Timeline */}
        <div style={styles.timelineSection}>
          <h3 style={styles.sectionTitle}>⏱️ Event Timeline</h3>
          
          <div style={styles.timelineGrid}>
            {/* Person Entered */}
            <div style={styles.timelineItem}>
              <div style={{
                ...styles.timelineIndicator,
                backgroundColor: videoAnalysis.person_entered ? '#10b981' : '#e5e7eb'
              }}>
                {videoAnalysis.person_entered ? '✓' : '○'}
              </div>
              <div style={styles.timelineInfo}>
                <span style={styles.timelineLabel}>Person Entered</span>
                <span style={{
                  ...styles.timelineValue,
                  color: videoAnalysis.person_entered ? '#10b981' : '#6b7280'
                }}>
                  {videoAnalysis.person_entered ? 'YES' : 'NO'}
                </span>
              </div>
            </div>

            {/* Person Stayed */}
            <div style={styles.timelineItem}>
              <div style={{
                ...styles.timelineIndicator,
                backgroundColor: videoAnalysis.person_stayed ? '#3b82f6' : '#e5e7eb'
              }}>
                {videoAnalysis.person_stayed ? '✓' : '○'}
              </div>
              <div style={styles.timelineInfo}>
                <span style={styles.timelineLabel}>Person Stayed</span>
                <span style={{
                  ...styles.timelineValue,
                  color: videoAnalysis.person_stayed ? '#3b82f6' : '#6b7280'
                }}>
                  {videoAnalysis.person_stayed ? 'YES' : 'NO'}
                </span>
              </div>
            </div>

            {/* Person Left */}
            <div style={styles.timelineItem}>
              <div style={{
                ...styles.timelineIndicator,
                backgroundColor: videoAnalysis.person_left ? '#f59e0b' : '#e5e7eb'
              }}>
                {videoAnalysis.person_left ? '✓' : '○'}
              </div>
              <div style={styles.timelineInfo}>
                <span style={styles.timelineLabel}>Person Left</span>
                <span style={{
                  ...styles.timelineValue,
                  color: videoAnalysis.person_left ? '#f59e0b' : '#6b7280'
                }}>
                  {videoAnalysis.person_left ? 'YES' : 'NO'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Motion Indicators */}
        <div style={styles.motionSection}>
          <h3 style={styles.sectionTitle}>🏃 Motion & Interaction</h3>
          
          <div style={styles.motionGrid}>
            {/* Plant Touched */}
            <div style={styles.motionItem}>
              <span style={styles.motionIcon}>
                {videoAnalysis.plant_touched ? '🤚' : '👋'}
              </span>
              <div style={styles.motionInfo}>
                <span style={styles.motionLabel}>Plant Touched</span>
                <span style={{
                  ...styles.motionValue,
                  color: videoAnalysis.plant_touched ? '#ef4444' : '#10b981'
                }}>
                  {videoAnalysis.plant_touched ? 'YES' : 'NO'}
                </span>
              </div>
            </div>

            {/* Plant Blocked */}
            <div style={styles.motionItem}>
              <span style={styles.motionIcon}>
                {videoAnalysis.plant_blocked ? '🚫' : '👁️'}
              </span>
              <div style={styles.motionInfo}>
                <span style={styles.motionLabel}>Plant Blocked</span>
                <span style={{
                  ...styles.motionValue,
                  color: videoAnalysis.plant_blocked ? '#f59e0b' : '#10b981'
                }}>
                  {videoAnalysis.plant_blocked ? 'YES' : 'NO'}
                </span>
              </div>
            </div>

            {/* Plant Visible Throughout */}
            <div style={styles.motionItem}>
              <span style={styles.motionIcon}>
                {videoAnalysis.plant_visible_throughout ? '✅' : '⚠️'}
              </span>
              <div style={styles.motionInfo}>
                <span style={styles.motionLabel}>Visible Throughout</span>
                <span style={{
                  ...styles.motionValue,
                  color: videoAnalysis.plant_visible_throughout ? '#10b981' : '#f59e0b'
                }}>
                  {videoAnalysis.plant_visible_throughout ? 'YES' : 'NO'}
                </span>
              </div>
            </div>

            {/* Significant Motion */}
            <div style={styles.motionItem}>
              <span style={styles.motionIcon}>
                {videoAnalysis.significant_motion ? '💨' : '🧘'}
              </span>
              <div style={styles.motionInfo}>
                <span style={styles.motionLabel}>Significant Motion</span>
                <span style={{
                  ...styles.motionValue,
                  color: videoAnalysis.significant_motion ? '#3b82f6' : '#6b7280'
                }}>
                  {videoAnalysis.significant_motion ? 'YES' : 'NO'}
                </span>
              </div>
            </div>
          </div>

          {/* Motion Description */}
          {videoAnalysis.motion_description && (
            <div style={styles.motionDescription}>
              <span style={styles.motionDescLabel}>Motion Details:</span>
              <p style={styles.motionDescText}>{videoAnalysis.motion_description}</p>
            </div>
          )}
        </div>

        {/* Person Tracking */}
        {(videoAnalysis.person_entered || videoAnalysis.person_stayed || videoAnalysis.person_left) && (
          <div style={styles.trackingSection}>
            <h3 style={styles.sectionTitle}>👤 Person Tracking</h3>
            
            <div style={styles.trackingTimeline}>
              {videoAnalysis.person_entered && (
                <div style={styles.trackingEvent}>
                  <div style={styles.trackingDot} />
                  <div style={styles.trackingContent}>
                    <span style={styles.trackingTime}>Start</span>
                    <span style={styles.trackingDesc}>Person entered frame</span>
                  </div>
                </div>
              )}
              
              {videoAnalysis.person_stayed && (
                <div style={styles.trackingEvent}>
                  <div style={{...styles.trackingDot, backgroundColor: '#3b82f6'}} />
                  <div style={styles.trackingContent}>
                    <span style={styles.trackingTime}>During</span>
                    <span style={styles.trackingDesc}>Person remained in frame</span>
                  </div>
                </div>
              )}
              
              {videoAnalysis.person_left && (
                <div style={styles.trackingEvent}>
                  <div style={{...styles.trackingDot, backgroundColor: '#f59e0b'}} />
                  <div style={styles.trackingContent}>
                    <span style={styles.trackingTime}>End</span>
                    <span style={styles.trackingDesc}>Person left frame</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div style={styles.metadata}>
          <div style={styles.metadataRow}>
            <span style={styles.label}>📅 Recorded:</span>
            <span style={styles.value}>
              {new Date(videoAnalysis.time).toLocaleString()}
            </span>
          </div>
          <div style={styles.metadataRow}>
            <span style={styles.label}>🎞️ Frames Analyzed:</span>
            <span style={styles.value}>{videoAnalysis.frames_analyzed || 0}</span>
          </div>
          <div style={styles.metadataRow}>
            <span style={styles.label}>🤖 Model:</span>
            <span style={styles.value}>{videoAnalysis.vlm_model || 'N/A'}</span>
          </div>
          <div style={styles.metadataRow}>
            <span style={styles.label}>📊 Status:</span>
            <span style={{
              ...styles.value,
              color: videoAnalysis.analysis_status === 'completed' ? '#10b981' : '#f59e0b',
              fontWeight: 'bold'
            }}>
              {videoAnalysis.analysis_status?.toUpperCase() || 'UNKNOWN'}
            </span>
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
  videoContainer: {
    width: '100%',
    backgroundColor: '#000',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
  },
  video: {
    width: '100%',
    maxHeight: '600px',
    objectFit: 'contain',
  },
  eventTypeSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'center',
  },
  eventTypeBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 24px',
    borderRadius: '24px',
    border: '2px solid',
  },
  eventTypeIcon: {
    fontSize: '24px',
  },
  eventTypeText: {
    fontSize: '18px',
    fontWeight: 'bold',
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
  timelineSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  timelineGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
  },
  timelineItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  timelineIndicator: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
    fontWeight: 'bold',
    color: 'white',
  },
  timelineInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  timelineLabel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
  },
  timelineValue: {
    fontSize: '14px',
    fontWeight: 'bold',
  },
  motionSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  motionGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '16px',
  },
  motionItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
  },
  motionIcon: {
    fontSize: '32px',
  },
  motionInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  motionLabel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
  },
  motionValue: {
    fontSize: '14px',
    fontWeight: 'bold',
  },
  motionDescription: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#f0f9ff',
    borderRadius: '8px',
    borderLeft: '4px solid #3b82f6',
  },
  motionDescLabel: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#1e40af',
    display: 'block',
    marginBottom: '8px',
  },
  motionDescText: {
    fontSize: '14px',
    color: '#1e40af',
    margin: 0,
    lineHeight: '1.5',
  },
  trackingSection: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#fef3c7',
  },
  trackingTimeline: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  trackingEvent: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
  },
  trackingDot: {
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    backgroundColor: '#10b981',
    marginTop: '4px',
    flexShrink: 0,
  },
  trackingContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  trackingTime: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#92400e',
  },
  trackingDesc: {
    fontSize: '14px',
    color: '#78350f',
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

export default VideoAnalysisCard;
