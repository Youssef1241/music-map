import { useMemo, useEffect, useState } from 'react';
import { loadMatrix } from '/public/data/loadMatrix';


export const POPULARITY_KEY = 'ARTIST_POPULARITY';

// Cached once the matrix loads — getNodeRadius is called from ArtistGraphCanvas
// on every animation frame, so it can't depend on hook-local state.
let cachedMaxPopularity = 10;
// Popularity value at the Nth percentile — outliers above this just clip
// to maxR instead of crushing everyone else toward minR. See computePopCap().
let cachedPopCap = 10;

function computePopCap(popularities, percentile = 0.97) {
  if (!popularities.length) return 1;
  const sorted = [...popularities].sort((a, b) => a - b);
  const idx = Math.floor(sorted.length * percentile);
  return sorted[Math.min(idx, sorted.length - 1)];
}

export function getNodeRadius(
  popularity,
  {
    isTarget = false,
    isHovered = false,
    viewMode = 'GLOBAL',
    popCap = cachedPopCap,
    exponent = 0.8,
  } = {}
) {
  const minR = viewMode === 'GLOBAL' ? 5 : 3;
  const maxR = viewMode === 'GLOBAL' ? 15 : 11;

  const rawPop = Math.max(popularity ?? 0, 0);
  const cap = Math.max(popCap, 1);

  // Clamp to the cap BEFORE normalizing so a handful of mega-artists
  // just top out at maxR instead of dragging the whole scale down.
  const clamped = Math.min(rawPop, cap);
  const norm = Math.pow(clamped / cap, exponent);

  let r = minR + norm * (maxR - minR);

  if (isTarget) r = Math.max(r * 1.25, viewMode === 'GLOBAL' ? 8 : 9);
  if (isHovered) r = Math.max(r * 1.1, viewMode === 'GLOBAL' ? 5 : 7);

  return r;
}

export function useArtistGraph(focalArtist, viewMode, fgRef, locale = 'ar') {

  const [matrix, setMatrix] = useState(null);

  useEffect(() => {
    loadMatrix().then((m) => {
      cachedMaxPopularity = m.getMaxPopularity();

      const allPopularities = m.getAllIds().map((id) => m.getPopularity(id));
      cachedPopCap = computePopCap(allPopularities, 0.95);

      setMatrix(m);
    });
  }, []);

  const graphData = useMemo(() => {
    if (!matrix) return { nodes: [], links: [] };

    if (viewMode === 'FOCUS') {

      const top100List = matrix
        .getFullRow(focalArtist)
        .slice(0, 100)

      const top100Ids = top100List.map((item) => item.id);
      const top100Set = new Set([focalArtist, ...top100Ids]);

      const nodes = Array.from(top100Set).map((id) => ({
        id,
        name:
          matrix.getName(id, locale) ||
          matrix.getName(id, locale === 'ar' ? 'en' : 'ar'),
        isTarget: id === focalArtist,
        popularity: matrix.getPopularity(id),
      }));

      const links = [];
      const processedPairs = new Set();

      // Primary Focal Links
      top100List.forEach((item) => {
        const pairKey = [focalArtist, item.id].sort().join('___');
        processedPairs.add(pairKey);
        links.push({
          source: focalArtist,
          target: item.id,
          similarity: item.similarity,
          isPrimary: true,
        });
      });

      // Inter-artist connections among top 100
      top100Ids.forEach((artistA) => {
        const peers = top100Ids
          .filter((id) => id !== artistA)
          .map((id) => ({ id, sim: matrix.getSimilarity(artistA, id) }))
          .filter((p) => p.sim !== undefined)
          .sort((a, b) => b.sim - a.sim)
          .slice(0, 2);

        peers.forEach((peer) => {
          const pairKey = [artistA, peer.id].sort().join('___');
          if (!processedPairs.has(pairKey)) {
            processedPairs.add(pairKey);
            links.push({
              source: artistA,
              target: peer.id,
              similarity: peer.sim,
              isPrimary: false,
            });
          }
        });
      });

      return { nodes, links };
    }

    // ==================== GLOBAL MODE ====================
    const allArtists = matrix.getAllIds();
    const nodes = allArtists.map((id) => ({
      id,
      name:
        matrix.getName(id, locale) ||
        matrix.getName(id, locale === 'ar' ? 'en' : 'ar'),
      isTarget: id === focalArtist,
      popularity: matrix.getPopularity(id),
    }));

    const links = [];
    const processedPairs = new Set();

    allArtists.forEach((artistA) => {
      const top2Peers = matrix.getTopN(artistA, 2);

      top2Peers.forEach((peer) => {
        const pairKey = [artistA, peer.id].sort().join('___');
        if (!processedPairs.has(pairKey)) {
          processedPairs.add(pairKey);
          links.push({
            source: artistA,
            target: peer.id, // Fix: Use peer.id here
            similarity: peer.similarity,
            isPrimary: false,
          });
        }
      });
    });

    return { nodes, links };
  }, [matrix, focalArtist, viewMode, locale]);


  // 2. Gentle post-layout drift — cheap rAF nudges instead of endless d3 simulation
  useEffect(() => {
    if (!fgRef.current || !graphData.nodes.length) return;

    const driftStrength = viewMode === 'GLOBAL' ? 0.035 : 0.06;
    let rafId = 0;

    const drift = () => {
      const fg = fgRef.current;
      if (!fg) return;

      const { nodes } = graphData;
      const t = performance.now() / 5000;

      for (const node of nodes) {
        if (node.fx != null || node.fy != null) continue;
        if (node.x == null || node.y == null) continue;

        const phase = node._floatPhase ?? (node._floatPhase = Math.random() * Math.PI * 2);
        node.x += Math.sin(t + phase) * driftStrength;
        node.y += Math.cos(t * 1.17 + phase * 1.4) * driftStrength;
      }

      rafId = requestAnimationFrame(drift);
    };

    const startTimer = setTimeout(() => {
      rafId = requestAnimationFrame(drift);
    }, 1800);

    return () => {
      clearTimeout(startTimer);
      cancelAnimationFrame(rafId);
    };
  }, [graphData, viewMode, fgRef]);

  return { graphData };
}