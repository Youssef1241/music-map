import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';

function MapPage() {
  const { artistName } = useParams();
  const navigate = useNavigate();
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMapData = async () => {
            setLoading(true);
        
        try{
            const url = `http://127.0.0.1:8000/get-similar?artist_name=${encodeURIComponent(artistName)}`;
            const response = await fetch(url);
            const data = await response.json();

            if(data.graphData){
                setGraphData(data.graphData);
            }
        } catch (error){
            console.error("Failed to load map network:", error);
        } finally {
            setLoading(false);
        }
        };
        fetchMapData();
    }, [artistName]);
  
return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative overflow-hidden">
      
      {/* Absolute Overlaid Floating Header */}
      <div className="absolute top-6 left-6 z-10 bg-slate-800/80 border border-slate-700/40 rounded-2xl p-4 shadow-2xl backdrop-blur-md flex items-center gap-4">
        <button 
          onClick={() => navigate('/')} 
          className="px-3 py-1.5 text-xs font-bold bg-slate-950 text-slate-400 rounded-lg hover:text-teal-400 border border-slate-800 transition-colors"
        >
          ← Back
        </button>
        <div>
          <h2 className="text-md font-bold text-teal-400">Mapping: {artistName}</h2>
          <p className="text-[10px] text-slate-400">Scroll to zoom • Click & drag nodes</p>
        </div>
      </div>

      {/* Canvas Workspace Container */}
      <div className="w-full flex-1 h-full min-h-screen">
        {loading ? (
          <div className="w-full h-full min-h-screen flex items-center justify-center text-slate-400 animate-pulse">
            🌐 Mapping connections inside DuckDB database...
          </div>
        ) : graphData ? (
          <ForceGraph2D
            graphData={graphData}
            nodeAutoColorBy="id"
            nodeVal={(node) => node.val}
            linkColor={() => '#334155'}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.id;
              const fontSize = 13 / globalScale;
              ctx.font = `${fontSize}px sans-serif`;
              ctx.fillStyle = node.color;
              
              ctx.beginPath();
              ctx.arc(node.x, node.y, node.val / 2, 0, 2 * Math.PI, false);
              ctx.fill();

              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = '#f8fafc';
              ctx.fillText(label, node.x, node.y + (node.val / 2) + 8);
            }}
            // ⚡ THE LAZY LOADING MAGIC TRICK:
            // Clicking any node automatically updates the browser URL, running the useEffect again!
            onNodeClick={(node) => {
              navigate(`/map/${encodeURIComponent(node.id)}`);
            }}
          />
        ) : (
          <div className="w-full h-full min-h-screen flex items-center justify-center text-rose-400">
            Failed to render map structure.
          </div>
        )}
      </div>

    </div>
  );
}

export default MapPage;