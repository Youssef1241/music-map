import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function SearchPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim() !== '') {
      navigate(`/map/${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center justify-center p-6">
      <div className="text-center mb-8 max-w-md">
        <h1 className="inline-block text-4xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent mb-3">
          خريطة الموسيقى العربية
        </h1>
        <p className="text-slate-400 text-lg">Arab Music Map</p>
      </div>


      <div className="w-full max-w-md bg-slate-800 border border-slate-700/50 rounded-2xl p-6 shadow-xl">
        <form onSubmit={handleSearchSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-slate-400">Search for an Artist</label>
            <input
              type="text"
              placeholder="e.g., Amr Diab, Wegz, Fairuz..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-xl focus:outline-none focus:border-teal-500 text-slate-100"
            />
          </div>
          <button type="submit" className="w-full py-3 bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 font-semibold rounded-xl transition-all active:scale-[0.98]">
            Explore Map
          </button>
        </form>
      </div>
    </div>
  );
}

// 🚨 CRITICAL: This allows App.jsx to read this component!
export default SearchPage;