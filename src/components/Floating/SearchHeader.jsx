import React, { useState } from 'react';
import { Search, CornerUpRight } from 'lucide-react';
import './SearchHeader.css';

const SearchHeader = ({ mapType, onMapTypeChange }) => {
    return (
        <div className="search-header-container">
            <div className="search-bar">
                <Search size={20} className="search-icon" />
                <input
                    type="text"
                    placeholder="Search address or user..."
                    className="search-input"
                />
                <div className="search-action">
                    <CornerUpRight size={18} />
                </div>
            </div>

            <div className="map-type-toggle">
                <button
                    className={`toggle-btn ${mapType === 'Map' ? 'active' : ''}`}
                    onClick={() => onMapTypeChange('Map')}
                >
                    Map
                </button>
                <button
                    className={`toggle-btn ${mapType === 'Satellite' ? 'active' : ''}`}
                    onClick={() => onMapTypeChange('Satellite')}
                >
                    Satellite
                </button>
            </div>
        </div>
    );
};

export default SearchHeader;
