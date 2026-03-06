import React, { useState, useEffect } from 'react'
import MainLayout from './components/Layout/MainLayout'
import AlertsPanel from './components/Layout/AlertsPanel'
import MapContainer from './components/Map/MapContainer'
import SearchHeader from './components/Floating/SearchHeader'
import DispatchPanel from './components/Floating/DispatchPanel'
import MessageModal from './components/Modals/MessageModal'
import DashboardPanel from './components/Dashboard/DashboardPanel'
import EarthquakePrediction from './components/Dashboard/EarthquakePrediction'
import DevicesPanel from './components/Devices/DevicesPanel'
import SettingsPanel from './components/Settings/SettingsPanel'
import UsersPanel from './components/Users/UsersPanel'
import './App.css'

import { fetchActiveSOS } from './services/api'
import { connectSOSWebSocket } from './services/websocket'

function App() {
  const [activeTab, setActiveTab] = useState('alerts');
  const [darkMode, setDarkMode] = useState(true);
  const [selectedAlertId, setSelectedAlertId] = useState(null);
  const [zones, setZones] = useState([]);
  const [isMessageModalOpen, setIsMessageModalOpen] = useState(false);
  const [messageRecipient, setMessageRecipient] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [checkpoints, setCheckpoints] = useState([]); // New state for RFID notifications

  // ... rest of history stays the same ...
  const [history, setHistory] = useState([
    { id: 101, user: 'Sanjay Dutt', avatar: '/avatars/male_1.png', location: 'Dhela Range', time: '10:15 AM', responseTime: '12 min', status: 'RESOLVED' },
    { id: 102, user: 'Priya Rai', avatar: '/avatars/female_1.png', location: 'Garjiya Gate', time: '09:30 AM', responseTime: '18 min', status: 'RESOLVED' },
    { id: 103, user: 'Karan Johar', avatar: '/avatars/male_2.png', location: 'Sitabani Buffer', time: 'Yesterday', responseTime: '24 min', status: 'RESOLVED' },
    { id: 104, user: 'Aditi Rao', avatar: '/avatars/female_2.png', location: 'Bijrani Range', time: '2 hours ago', responseTime: '15 min', status: 'RESOLVED' }
  ]);

  const addZone = (zone) => {
    setZones(prev => [...prev, { ...zone, id: Date.now() }]);
  };

  const handleSelectAlert = (id) => {
    setSelectedAlertId(id);
    setActiveTab('alerts');
  };

  const handleSendMessage = (user) => {
    setMessageRecipient(user);
    setIsMessageModalOpen(true);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  // Initial Data Fetch & WebSocket Setup
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
            position: [event.location_data?.[0]?.latitude || 30.6830, event.location_data?.[0]?.longitude || 76.6058],
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
          setAlerts(formattedAlerts);
        }
      } catch (error) {
        console.error("Failed to load active SOS:", error);
      }
    };

    loadInitialData();

    const ws = connectSOSWebSocket((data) => {
      console.log("WebSocket Message Received:", data);

      if (data.type === 'sos_alert' || data.type === 'telemetry_update' || data.type === 'pulse_alert') {
        console.log("Triggering SOS/Telemetry Update UI...");
        setActiveTab('alerts');

        setAlerts(prev => {
          // Identify unique SOS card by event_id or device_id fallback
          const uniqueId = data.event_id || data.device_id;
          const existingIndex = prev.findIndex(a => (data.event_id && a.id === data.event_id) || (!data.event_id && a.device === data.device_id));

          if (existingIndex !== -1) {
            // Update existing SOS card
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
            // Move updated item to top
            updated.splice(existingIndex, 1);
            return [item, ...updated];
          } else if (data.sos || data.type === 'sos_alert') {
            // Create new SOS card
            const newId = data.event_id || Date.now();
            setSelectedAlertId(newId);
            return [{
              id: newId,
              type: 'sos',
              user: data.device_id === 'midway_panel' ? 'Midway Panel' : `User ${data.device_id}`,
              avatar: data.device_id === 'midway_panel' ? '/avatars/male_1.png' : '/avatars/male_2.png',
              device: data.device_id,
              status: 'SOS ACTIVE',
              position: data.latitude ? [data.latitude, data.longitude] : [30.6830, 76.6058],
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

        // Remove after 5 seconds
        setTimeout(() => {
          setCheckpoints(prev => prev.filter(cp => cp.id !== newCheckpoint.id));
        }, 5000);
      }
    });


    return () => {
      ws.close();
    };
  }, []);

  // Global Zoom Blocker to prevent whole website from zooming
  useEffect(() => {
    const preventZoom = (e) => {
      if (e.ctrlKey || (e.type === 'wheel' && Math.abs(e.deltaY) < 10)) {
        if (!e.target.closest('.map-container')) {
          e.preventDefault();
        }
      }
    };
    window.addEventListener('wheel', preventZoom, { passive: false });
    return () => window.removeEventListener('wheel', preventZoom);
  }, []);

  const [mapType, setMapType] = useState('Satellite');

  const selectedAlert = alerts.find(a => a.id === selectedAlertId) || alerts.find(a => a.type === 'sos');

  const renderSidePanel = () => {
    const commonProps = { onClose: () => setActiveTab('map') };
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPanel alerts={alerts} {...commonProps} />;
      case 'alerts':
        return <AlertsPanel alerts={alerts} history={history} selectedId={selectedAlertId} onSelectAlert={handleSelectAlert} {...commonProps} />;
      case 'earthquake':
        return <EarthquakePrediction {...commonProps} />;
      case 'devices':
        return <DevicesPanel {...commonProps} />;
      case 'settings':
        return <SettingsPanel darkMode={darkMode} onThemeToggle={() => setDarkMode(!darkMode)} {...commonProps} />;
      case 'users':
        return <UsersPanel {...commonProps} />;
      default:
        return null;
    }
  };

  return (
    <MainLayout activeTab={activeTab} onTabChange={(tab) => {
      if (tab === activeTab && tab !== 'map') {
        setActiveTab('map');
      } else if (['dashboard', 'alerts', 'map', 'settings', 'devices', 'users', 'earthquake'].includes(tab)) {
        setActiveTab(tab);
      }
    }}>
      <div className={`main-content-split ${activeTab === 'map' ? 'view-map' : 'view-panel'}`}>
        {activeTab !== 'map' && (
          <div className="side-panel-container">
            {renderSidePanel()}
          </div>
        )}
        <div className={`map-wrapper ${activeTab === 'map' ? 'full-width' : 'partial-width'}`}>
          <MapContainer
            alerts={alerts}
            mapType={mapType}
            onSelectAlert={handleSelectAlert}
            onSendMessage={(user) => handleSendMessage(user)}
            selectedId={selectedAlertId}
            zones={zones}
            onAddZone={addZone}
          />
          <SearchHeader mapType={mapType} onMapTypeChange={setMapType} />
          {selectedAlert && (
            <DispatchPanel
              alert={selectedAlert}
              onSendMessage={() => handleSendMessage(selectedAlert.user)}
            />
          )}
        </div>
      </div>

      <MessageModal
        isOpen={isMessageModalOpen}
        onClose={() => setIsMessageModalOpen(false)}
        recipient={messageRecipient}
      />

      {/* Checkpoint Notifications Overlay */}
      <div className="checkpoint-overlay">
        {checkpoints.map(cp => (
          <div key={cp.id} className="checkpoint-toast">
            <div className="checkpoint-toast-icon">📍</div>
            <div className="checkpoint-toast-content">
              <strong>Checkpoint Reached</strong>
              <span>{cp.user} checked in at {cp.location}</span>
              <small>{cp.time}</small>
            </div>
          </div>
        ))}
      </div>
    </MainLayout>
  )
}

export default App
