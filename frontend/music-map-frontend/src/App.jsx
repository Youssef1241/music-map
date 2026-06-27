import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SearchPage from './components/SearchPage';
import MapPage from './components/MapPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SearchPage />} />        
        <Route path="/map/:artistName" element={<MapPage />} />
      </Routes>
    </BrowserRouter>
  );
}