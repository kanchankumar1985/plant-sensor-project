import { useState, useEffect } from 'react';

export default function TouchStatusCard() {
  const [touchStatus, setTouchStatus] = useState({
    state: 'NOT_TOUCHED',
    timestamp: null,
    is_touched: false,
    device_id: 'plant-esp32-01',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTouchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/touch/latest');
      if (!response.ok) {
        if (response.status === 404) {
          // No events yet
          setTouchStatus({
            state: 'NOT_TOUCHED',
            timestamp: null,
            seconds_ago: null,
          });
          setError(null);
          setIsLoading(false);
          return;
        }
        throw new Error('Failed to fetch touch status');
      }
      const data = await response.json();
      setTouchStatus({
        state: data.state,
        timestamp: data.timestamp,
        seconds_ago: data.seconds_ago,
        is_touched: data.state === 'TOUCHED',
      });
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching touch status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchTouchStatus();

    // Poll every 2 seconds
    const interval = setInterval(fetchTouchStatus, 2000);

    return () => clearInterval(interval);
  }, []);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-800">Touch Sensor</h2>
        <div className="text-sm text-gray-500">
          {touchStatus.device_id}
        </div>
      </div>

      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          {/* Status Indicator */}
          <div className="mb-4 flex justify-center">
            <div
              className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
                touchStatus.is_touched
                  ? 'bg-green-500 shadow-lg shadow-green-500/50 animate-pulse'
                  : 'bg-gray-300'
              }`}
            >
              <span className="text-4xl">
                {touchStatus.is_touched ? '👆' : '🖐️'}
              </span>
            </div>
          </div>

          {/* Status Text */}
          <div className="mb-2">
            <span
              className={`text-2xl font-bold ${
                touchStatus.is_touched ? 'text-green-600' : 'text-gray-500'
              }`}
            >
              {touchStatus.state}
            </span>
          </div>

          {/* Timestamp */}
          <div className="text-sm text-gray-500">
            Last updated: {formatTimestamp(touchStatus.timestamp)}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 text-sm text-red-500">
              ⚠️ {error}
            </div>
          )}
        </div>
      </div>

      {/* Live Indicator */}
      <div className="flex items-center justify-center mt-4 text-xs text-gray-400">
        <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
        LIVE
      </div>
    </div>
  );
}
