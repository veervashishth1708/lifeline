import React, { useState, useEffect } from 'react';
import { Phone, MessageSquare, ArrowRight, X, MapPin } from 'lucide-react';
import './AlertsPanel.css';

const AlertsPanel = ({ alerts = [], history = [], selectedId, onClose, onSelectAlert }) => {
    const [activeTab, setActiveTab] = useState('active');

    // Auto-scroll to selected alert if it changes
    useEffect(() => {
        if (selectedId) {
            const element = document.getElementById(`alert-card-${selectedId}`);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }, [selectedId]);

    const renderAlertsList = () => {
        if (activeTab === 'active') {
            const activeAlerts = alerts.filter(alert => alert.type !== 'safe');

            if (activeAlerts.length === 0) {
                return (
                    <div className="empty-alerts-state">
                        <div className="empty-icon">🔔</div>
                        <h3>No Active SOS</h3>
                        <p>Waiting for signals from Nodes A, B, or C...</p>
                        <small>Check hardware connections if signal is expected.</small>
                    </div>
                );
            }

            return activeAlerts.map(alert => (
                <div
                    key={alert.id}
                    id={`alert-card-${alert.id}`}
                    className={`alert-card ${alert.type} ${selectedId === alert.id ? 'selected-highlight' : ''}`}
                >
                    <div className="alert-header">
                        <div className="alert-header-main">
                            <h3 className="user-dest">
                                {alert.user} <ArrowRight size={14} /> {alert.destination || 'N/A'}
                            </h3>
                            {alert.type === 'sos' && (
                                <div className="vitals-row">
                                    <div className="vitals-inline">
                                        <div className="vital-mini-box pulse">
                                            <span className="val">{alert.details?.pulse || '112 BPM'}</span>
                                        </div>
                                        {alert.device !== 'midway_panel' && (
                                            <div className="vital-mini-box speed">
                                                <span className="val">{alert.details?.speed || '1.2 km/h'}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="alert-header-meta">
                            <span className="device-id">Device ID {alert.device}</span>
                            <span className={`status-badge ${alert.type}`}>{alert.status}</span>
                        </div>
                    </div>

                    {(alert.type === 'sos' || selectedId === alert.id) && (
                        <div className="alert-details-body">
                            <div className="live-location-section">
                                <div className="live-loc-header">
                                    <span className="label">Live Location</span>
                                    <button
                                        className="open-loc-btn"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onSelectAlert && onSelectAlert(alert.id);
                                        }}
                                        title="View on Map"
                                    >
                                        <MapPin size={14} />
                                    </button>
                                </div>
                                <div className="loc-value-box">
                                    <span className="loc-val-badge">
                                        {alert.destination === 'N/A' || !alert.destination ? 'N/A' : alert.destination}
                                    </span>
                                </div>
                            </div>

                            <div className="detail-grid">
                                <div className="detail-item">
                                    <span className="label">SENSOR TYPE</span>
                                    <span className="value">{alert.details?.sensor || 'GPS Tracking'}</span>
                                </div>
                                <div className="detail-item">
                                    <span className="label">LAST HEARTBEAT</span>
                                    <span className="value">{alert.details?.heartbeat || 'Live'}</span>
                                </div>
                                <div className="detail-item">
                                    <span className="label">BATTERY STATUS</span>
                                    <span className="value success">{alert.details?.battery || '90%'}</span>
                                </div>
                            </div>

                            {alert.team && (
                                <div className="team-status-alert">
                                    <div className="team-main-info">
                                        <span className="label">TEAM STATUS</span>
                                        <span className="value team-status">{alert.team.status}</span>
                                    </div>
                                    <div className="team-eta-info">
                                        <span className="label">ETA</span>
                                        <span className="value eta">{alert.team.eta}</span>
                                    </div>
                                </div>
                            )}

                            <div className="assigned-contact">
                                <div className="avatar">
                                    <img src={alert.avatar} alt={alert.user} />
                                </div>
                                <div className="contact-info">
                                    <span className="label">ASSIGNED CONTACT</span>
                                    <span className="name">{alert.assigned || alert.user}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {alert.type === 'sos' && <div className="sos-glow-border"></div>}
                </div>
            ));
        } else {
            // History Tab
            if (history.length === 0) {
                return (
                    <div className="empty-alerts-state">
                        <div className="empty-icon">📂</div>
                        <h3>No History Yet</h3>
                        <p>Resolved events will appear here.</p>
                    </div>
                );
            }

            return history.map(item => (
                <div key={item.id} className="alert-card history">
                    <div className="alert-header">
                        <div className="avatar-mini">
                            <img src={item.avatar} alt={item.user} />
                        </div>
                        <div className="alert-info">
                            <h3>{item.user} <ArrowRight size={14} /> {item.location}</h3>
                            <span className="device-id">Resolved at {item.time}</span>
                        </div>
                        <span className="status-badge safe">{item.status}</span>
                    </div>
                    <div className="alert-details-body">
                        <div className="detail-item">
                            <span className="label">HELP REACHED IN</span>
                            <span className="value success">{item.responseTime}</span>
                        </div>
                    </div>
                </div>
            ));
        }
    };

    return (
        <div className="alerts-panel">
            <div className="panel-header">
                <div className="panel-title-row">
                    <h2>Emergency Alerts</h2>
                    <div className="panel-header-actions">
                        <button className="icon-btn-small">⋮</button>
                        <button className="icon-btn-small close-btn" onClick={onClose} title="Close Panel">
                            <X size={18} />
                        </button>
                    </div>
                </div>

                <div className="segmented-control">
                    <button
                        className={`segment-btn ${activeTab === 'active' ? 'active' : ''}`}
                        onClick={() => setActiveTab('active')}
                    >
                        Active SOS
                    </button>
                    <button
                        className={`segment-btn ${activeTab === 'history' ? 'active' : ''}`}
                        onClick={() => setActiveTab('history')}
                    >
                        History
                    </button>
                </div>
            </div>

            <div className="alerts-list">
                {renderAlertsList()}
            </div>
        </div>
    );
};

export default AlertsPanel;
