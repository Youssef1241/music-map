import React, { useRef, useState, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useArtistGraph, getNodeRadius } from './useArtistGraph.jsx';
import { forceCollide } from 'd3-force';
import { loadMatrix } from '../../public/data/loadMatrix.js';

// Hash string to pseudo-random float between 0 and 1
function hashStringToUnitFloat(value) {
  const str = String(value);
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return (Math.abs(hash) % 10000) / 10000;
}

// Replicates Search Page logic: 15% Amber (35-45 hue), 85% Teal/Cyan (180-260 hue)
function getNodeColorProps(str) {
  const rand1 = hashStringToUnitFloat(str);
  const rand2 = hashStringToUnitFloat(str + '_hue_offset');

  const isAmber = rand1 < 0.15; // 15% chance
  let hue, saturation, lightness;

  if (isAmber) {
    hue = 35 + rand2 * 10;
    saturation = 65;
    lightness = 48;
  } else {
    hue = 180 + rand2 * 80;
    saturation = 85;
    lightness = 52;
  }

  return { hue, saturation, lightness, isAmber };
}

export default function ArtistGraphCanvas({ viewMode, focalArtist, onNodeClick, locale = 'ar' }) {
  const fgRef = useRef();
  const [hoverNode, setHoverNode] = useState(null);
  const { graphData } = useArtistGraph(focalArtist, viewMode, fgRef, locale);
  const [matrix, setMatrix] = useState(null);

  useEffect(() => {
    loadMatrix().then(setMatrix);
  }, []);

  // Tune the physics whenever the graph (re)loads or mode changes
  useEffect(() => {
    if (!fgRef.current) return;

    // Stronger repulsion so unconnected nodes push apart more
    fgRef.current.d3Force('charge')
      .strength(viewMode === 'FOCUS' ? -800 : -800)
      .distanceMax(2000); // limits how far the repulsion reaches, keeps it from feeling chaotic

    // Collision force prevents nodes from ever visually overlapping,
    // sized to each node's actual drawn radius + a little breathing room
    fgRef.current.d3Force('collision', forceCollide(node =>
      getNodeRadius(node.popularity, { isTarget: node.isTarget && viewMode === 'FOCUS', viewMode }) + 18
    ));

    // Give links a bit more resting length so connected clusters aren't cramped
    const linkForce = fgRef.current.d3Force('link');
    if (linkForce) linkForce.distance(viewMode === 'FOCUS' ? 250 : 200);

    // Reheat the sim so the new forces actually take effect
    fgRef.current.d3ReheatSimulation();
    }, [graphData, viewMode]);

  return (
    <ForceGraph2D
      ref={fgRef}
      graphData={graphData}
      linkColor={(link) => {
        const isConnected = hoverNode && (link.source.id === hoverNode.id || link.target.id === hoverNode.id);
        if (isConnected) {
          return 'rgba(141, 64, 249)'
          }
        else{
        return viewMode === 'GLOBAL' ? 'rgba(148,163,184,0.4)' : 'rgba(3, 121, 86, 0.5)';
        }
      }}
      linkWidth={(link) => {
        const isConnected = hoverNode && (link.source.id === hoverNode.id || link.target.id === hoverNode.id);
        return isConnected ? 2.5 : 0.8;
      }}
      // linkWidth={0.8}
      linkDirectionalParticles={viewMode === 'FOCUS' ? 2 : 1}
      linkDirectionalParticleSpeed={0.0005}
      linkDirectionalParticleWidth={1}
      linkDirectionalParticleColor={() => 'rgb(141, 64, 249)'}
      linkCanvasObjectMode={() => 'after'}
      linkCanvasObject={(link, ctx, globalScale) => {
        if (!hoverNode || !matrix) return;
        const isConnected = link.source.id === hoverNode.id || link.target.id === hoverNode.id;
        if (!isConnected) return;

        const midX = (link.source.x + link.target.x) / 2;
        const midY = (link.source.y + link.target.y) / 2;
        const label = `${matrix.getSimilarityPercentile(link.similarity)}%`;
        if (!label) return;

        const fontSize = 11 / globalScale;
        ctx.font = `${fontSize}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // small backing pill so the number stays legible over links/nodes
        const padding = 3 / globalScale;
        const textWidth = ctx.measureText(label).width;
        ctx.fillStyle = 'rgba(2, 6, 23, 0.85)';
        ctx.fillRect(
          midX - textWidth / 2 - padding,
          midY - fontSize / 2 - padding,
          textWidth + padding * 2,
          fontSize + padding * 2
        );

        ctx.fillStyle = '#fbbf24';
        ctx.fillText(label, midX, midY);
      }}
      d3AlphaDecay={0.02}
      d3VelocityDecay={0.4}
      warmupTicks={20}
      cooldownTicks={200}
      onNodeHover={(node) => setHoverNode(node || null)}
      nodeCanvasObject={(node, ctx, globalScale) => {
        if (node.x == null || node.y == null) return;

            const isTarget = node.isTarget && viewMode === 'FOCUS';
            const isHovered = hoverNode && hoverNode.id === node.id;
            const radius = getNodeRadius(node.popularity, { isTarget, isHovered, viewMode });
            const label = node.name;

          // Compute node color property deterministically from node.id
            const colorProps = getNodeColorProps(node.id);
            const { hue, saturation, lightness, isAmber } = colorProps;

            // const hue = hueFromString(node.id);
            const seed = hue; // reuse existing hash so no extra computation
            const t = performance.now() / 1000;

            // Gentle vertical bob — different phase per node via `seed`
            const bobOffset = Math.sin(t * 1.5 + seed) * 1.5; // px
            

            // Gentle pulse on radius — swirl "breathing"
            const pulse = 1 + Math.sin(t * 1.5 + seed) * 0.04; // ±4% size

            const drawY = node.y + bobOffset;
            const drawRadius = radius * pulse;

            // Keep text sized consistently relative to the canvas scale so it doesn't shrink into obscurity
            const fontSize = (isTarget || isHovered ? 15 : 12) / globalScale;

            // Distance-based Radial Fog Glow on Focused/Hovered Node
            const glowRadius = radius + 5;
            const gradient = ctx.createRadialGradient(
              node.x,
              drawY,
              drawRadius,
              node.x,
              drawY,
              glowRadius
            );

            const glowColor = isAmber 
            ? `hsla(${hue}, ${saturation}%, ${lightness}%, 0.35)`
            : `hsla(${hue}, ${saturation}%, ${lightness}%, 0.35)`;

            gradient.addColorStop(0, isTarget ? 'rgba(45, 212, 191, 0.4)' : glowColor);
            gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

            ctx.beginPath();
            ctx.arc(node.x, drawY, glowRadius, 0, 2 * Math.PI, false);
            ctx.fillStyle = gradient;
            ctx.fill();

            
            // Draw Base Node Body (Swirly marbled orb)
            // Draw Base Node Body (marbled streak orb)
            let nodeFill;

            if (isTarget) {
              nodeFill = 'rgb(45, 213, 23)';
            } else if (isHovered) {
              nodeFill = 'rgb(197, 0, 33)';
            } else {
              const hue2 = hue + 20; // small offset — stays in-family instead of jumping across the wheel

              // Angle the gradient per-node so streaks don't all point the same way
              const angle = (hue / 360) * Math.PI * 2 + t * 0.3; // slowly rotates
              const dx = Math.cos(angle) * drawRadius;
              const dy = Math.sin(angle) * drawRadius;

              const marble = ctx.createLinearGradient(
                node.x - dx, drawY - dy,
                node.x + dx, drawY + dy
              );
              marble.addColorStop(0, `hsl(${hue}, ${saturation}%, ${lightness}%)`);
              marble.addColorStop(0.5, `hsl(${hue2}, ${saturation}%, ${lightness + 6}%)`);
              marble.addColorStop(1, `hsl(${hue}, ${saturation - 10}%, ${lightness - 15}%)`);
              nodeFill = marble;
            }

            ctx.beginPath();
            ctx.arc(node.x, drawY, drawRadius, 0, 2 * Math.PI, false);
            ctx.fillStyle = nodeFill;
            ctx.fill();

            // subtle shine overlay to keep the 3D orb feel
            const shine = ctx.createRadialGradient(
              node.x - drawRadius * 0.4, drawY - drawRadius * 0.4, 0,
              node.x, drawY, drawRadius
            );
            shine.addColorStop(0, 'rgba(255,255,255,0.35)');
            shine.addColorStop(0.4, 'rgba(255,255,255,0)');
            ctx.beginPath();
            ctx.arc(node.x, drawY, drawRadius, 0, 2 * Math.PI, false);
            ctx.fillStyle = shine;
            ctx.fill();

            if (isTarget || isHovered) {
              ctx.lineWidth = 1 / globalScale;
              ctx.strokeStyle = '#ffffff';
              ctx.stroke();
            }

            // In GLOBAL mode, only draw labels once zoomed in enough (or the node is hovered).
            // In FOCUS mode, always draw labels.
            const ZOOM_LABEL_THRESHOLD = 0.6; // tune to taste — higher = must zoom in more
            const shouldShowLabel =
              viewMode === 'FOCUS' || isHovered || globalScale >= ZOOM_LABEL_THRESHOLD;

            if (shouldShowLabel) {
              ctx.font = `${isTarget || isHovered ? 'bold ' : ''}${fontSize}px sans-serif`;
              ctx.textAlign = 'center';
              ctx.textBaseline = 'top';
              // ctx.fillStyle = isTarget ? '#2dd4bf' : isHovered ? '#f43f5e' : (isAmber ? '#fcd34d' : '#cbd5e1');
              ctx.fillStyle = '#ffffff'
              ctx.fillText(label, node.x, node.y + radius + (2 / globalScale));
            }

      }}
      nodePointerAreaPaint={(node, color, ctx) => {
            if (node.x == null || node.y == null) return;

            const radius = getNodeRadius(node.popularity, {
              isTarget: node.isTarget && viewMode === 'FOCUS',
              viewMode,
            }) + 2;
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
            ctx.fill();
      }}
      onNodeClick={onNodeClick}
    />
  );
}