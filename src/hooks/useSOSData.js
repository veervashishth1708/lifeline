import { useState, useEffect } from 'react';
import { fetchActiveSOS } from '../services/api';
import { connectSOSWebSocket } from '../services/websocket';

export const useSOSData = () => {
  const [alerts, setAlerts] = useState([]);
  const [checkpoints, setCheckpoints] = useState([]);
  const [deviceTelemetry, setDeviceTelemetry] = useState({});
  const [selectedAlertId, setSelectedAlertId] = useState(null);

  // Load Initial SOS Data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const activeSOS = await fetchActiveSOS();
        if (activeSOS.length > 0) {
          const formattedAlerts = activeSOS.map(event => ({
            id: event.id,
            type: 'sos',
            user: `User ${event.device_id}`,
            avatar: '/avatars/male_2.png',
            destination: 'Live Location',
            device: event.device_id,
            status: 'SOS ACTIVE',
            position: [event.location_data?.[0]?.latitude || 29.210347, event.location_data?.[0]?.longitude || 77.015948],
            details: {
              pulse: event.pulse_data?.[0]?.bpm ? `${event.pulse_data[0].bpm} BPM` : 'N/A',
              heartbeat: 'Just now',
              speed: '1.2 km/h',
              battery: '90%',
              sensor: 'GPS Tracking'
            },
            team: {
              status: 'DISPATCHED',
              eta: '8 mins'
            },
            assigned: 'Amit Verma'
          }));
          setAlerts(prev => [...formattedAlerts, ...prev]);
        }
      } catch (error) {
        console.error("Failed to load active SOS:", error);
      }
    };

    loadInitialData();

    // Setup WebSocket
    const ws = connectSOSWebSocket((data) => {
      console.log("WebSocket Message Received:", data);

      if (data.type === 'sos_alert' || data.type === 'telemetry_update' || data.type === 'pulse_alert') {
        if (data.device_id) {
          setDeviceTelemetry(prev => ({
            ...prev,
            [data.device_id]: {
              pulse: data.pulse,
              latitude: data.latitude,
              longitude: data.longitude,
              timestamp: data.timestamp || new Date().toISOString()
            }
          }));
        }

        setAlerts(prev => {
          const existingIndex = prev.findIndex(a => (data.event_id && a.id === data.event_id) || (!data.event_id && a.device === data.device_id));

          if (existingIndex !== -1) {
            const updated = [...prev];
            const item = {
              ...updated[existingIndex],
              position: data.latitude ? [data.latitude, data.longitude] : updated[existingIndex].position,
              status: 'SOS ACTIVE',
              details: {
                ...updated[existingIndex].details,
                pulse: data.pulse !== undefined ? `${data.pulse} BPM` : updated[existingIndex].details.pulse,
                heartbeat: 'Just now',
                battery: data.battery !== undefined ? `${data.battery}%` : updated[existingIndex].details.battery
              }
            };
            updated.splice(existingIndex, 1);
            return [item, ...updated];
          } else if (data.sos || data.type === 'sos_alert') {
            const newId = data.event_id || Date.now();
            setSelectedAlertId(newId);
            return [{
              id: newId,
              type: 'sos',
              user: data.device_id === 'midway_panel' ? 'Midway Panel' : `User ${data.device_id}`,
              avatar: data.device_id === 'midway_panel' ? '/avatars/male_1.png' : '/avatars/male_2.png',
              device: data.device_id,
              status: 'SOS ACTIVE',
              position: data.latitude ? [data.latitude, data.longitude] : [29.210347, 77.015948],
              details: {
                pulse: data.pulse !== undefined ? `${data.pulse} BPM` : 'N/A',
                heartbeat: 'Just now',
                speed: data.device_id === 'midway_panel' ? null : '0.0 km/h',
                battery: data.battery !== undefined ? `${data.battery}%` : '92%',
                sensor: data.device_id === 'midway_panel' ? 'Control Gateway' : 'GPS Tracking'
              },
              team: { status: 'DISPATCHED', eta: '12 mins' },
              assigned: 'Quick Response Team'
            }, ...prev];
          }
          return prev;
        });
      } else if (data.type === 'checkpoint_reached') {
        const newCheckpoint = {
          id: Date.now(),
          user: data.user_id || 'Unknown User',
          location: data.device_id,
          time: new Date().toLocaleTimeString()
        };

        setCheckpoints(prev => [newCheckpoint, ...prev]);
        setTimeout(() => {
          setCheckpoints(prev => prev.filter(cp => cp.id !== newCheckpoint.id));
        }, 5000);
      }
    });

    return () => {
      ws.close();
    };
  }, []);

  return {
    alerts,
    setAlerts,
    checkpoints,
    deviceTelemetry,
    selectedAlertId,
    setSelectedAlertId
  };
};
