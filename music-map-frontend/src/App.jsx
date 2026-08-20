import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SearchPage from './components/SearchPage';
import FocusMapPage from './components/FocusMapPage';
import GlobalMapPage from './components/GlobalMapPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SearchPage />} />        
        <Route path="/map" element={<GlobalMapPage />} />
        <Route path="/map/:artistId" element={<FocusMapPage />} />
      </Routes>
    </BrowserRouter>
  );
}