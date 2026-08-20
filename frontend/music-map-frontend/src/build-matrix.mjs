// scripts/build-matrix.mjs
//
// Converts a symmetric similarity-matrix JSON (string-int ids as keys,
// each mapping to { otherId: sim, ..., ARTIST_POPULARITY: n }) into:
//
//   1. artist-index.json   — small file: [{ id, name, popularity }, ...] in row order
//   2. similarity-matrix.bin — raw Float32Array, n x n, row-major, no keys/strings at all
//
// Run with:  node scripts/build-matrix.mjs <input.json> <artistNames.json> <outDir>

import { readFileSync, writeFileSync } from 'fs';
import { resolve } from 'path';

const POPULARITY_KEY = 'ARTIST_POPULARITY';

const [, , inputPath, namesPath, namesPathEn, outDir] = process.argv;

if (!inputPath || !namesPath || !outDir) {
  console.error(
    'Usage: node build-matrix.mjs <symmetric-matrix.json> <artistNames.json> <outDir>'
  );
  process.exit(1);
}

const matrixData = JSON.parse(readFileSync(resolve(inputPath), 'utf-8'));
const nameToId = JSON.parse(readFileSync(resolve(namesPath), 'utf-8'));
const nameToIdEn = JSON.parse(readFileSync(resolve(namesPathEn), 'utf-8'));

// Invert name->id into id->name for output
const idToName = {};
for (const [name, id] of Object.entries(nameToId)) {
  idToName[String(id)] = name;
}

const idToNameEn = {};
for (const [name, id] of Object.entries(nameToIdEn)) {
  idToNameEn[String(id)] = name;
}
// Stable, deterministic row order: numeric sort of ids.
// Drop any id that has no matching name — we can't render or search for a
// node with no display name, so it's better to exclude it here than carry
// a null through to the frontend.
const allIds = Object.keys(matrixData).sort((a, b) => Number(a) - Number(b));
const ids = allIds.filter((id) => Boolean(idToName[id]));
const droppedForNoName = allIds.length - ids.length;
const n = ids.length;

if (droppedForNoName > 0) {
  console.warn(
    `Dropping ${droppedForNoName} artist(s) with no matching name in artistNames.json (present in matrix but not in the name map)`
  );
}

console.log(`Found ${n} named artists. Building dense ${n}x${n} matrix...`);

const idToRow = {};
ids.forEach((id, i) => {
  idToRow[id] = i;
});

// Dense symmetric matrix, row-major, Float32
const matrix = new Float32Array(n * n);
const popularity = new Float32Array(n);
const simValues = []; 

ids.forEach((id, i) => {
  const row = matrixData[id];
  popularity[i] = row?.[POPULARITY_KEY] ?? 0;

  for (const [otherId, sim] of Object.entries(row)) {
    if (otherId === POPULARITY_KEY) continue;
    const j = idToRow[otherId];
    if (j === undefined) continue;

    const value = Number(sim) || 0;
    matrix[i * n + j] = value;
    matrix[j * n + i] = value;
    simValues.push(value);
  }
});

// --- Compute a rank-based lookup for percentage display ---
// Linear min/max scaling only works if the underlying values actually spread
// out. Ranking against *every* pair (most of which are barely related) makes
// the top-100-per-artist connections shown in the UI cluster near 100% —
// technically true, but uninformative. Ranking against only *this artist's*
// shown connections fixes the spread but forces whoever's weakest among them
// down to an artificial 0%, even though they're still meaningfully connected.
//
// The fix: rank against the population that's actually ever displayed —
// every artist's top-100 nearest neighbors, pooled together, dataset-wide.
// That excludes the huge mass of irrelevant pairs (so things spread out)
// without forcing an artificial floor on any single artist's weakest match.
const TOP_K = 100;
const relevantValues = [];

ids.forEach((id, i) => {
  const rowStart = i * n;
  const rowValues = [];
  for (let j = 0; j < n; j++) {
    if (j === i) continue;
    const v = matrix[rowStart + j];
    if (v > 0) rowValues.push(v);
  }
  rowValues.sort((a, b) => b - a);
  for (let k = 0; k < Math.min(TOP_K, rowValues.length); k++) {
    relevantValues.push(rowValues[k]);
  }
});

const NUM_BREAKPOINTS = 1000;
relevantValues.sort((a, b) => a - b);
const breakpoints = new Array(NUM_BREAKPOINTS);
for (let k = 0; k < NUM_BREAKPOINTS; k++) {
  const idx = Math.min(
    relevantValues.length - 1,
    Math.floor((k / NUM_BREAKPOINTS) * relevantValues.length)
  );
  breakpoints[k] = relevantValues[idx];
}

const similarityStats = {
  min: relevantValues[0] ?? 0,
  max: relevantValues[relevantValues.length - 1] ?? 1,
  breakpoints,
};

// --- Write outputs ---

const indexOut = ids.map((id, i) => ({
  id: Number(id),
  name: idToName[id],
  name_en: idToNameEn[id],
  popularity: popularity[i],
}));

writeFileSync(resolve(outDir, 'artist-index.json'), JSON.stringify(indexOut));
writeFileSync(resolve(outDir, 'similarity-matrix.bin'), Buffer.from(matrix.buffer));
writeFileSync(resolve(outDir, 'similarity-stats.json'), JSON.stringify(similarityStats));

const matrixMB = (matrix.byteLength / 1024 / 1024).toFixed(2);
console.log(`Wrote artist-index.json (${n} entries)`);
console.log(`Wrote similarity-matrix.bin (${matrixMB} MB, ${n}x${n} Float32)`);
console.log(
  `Wrote similarity-stats.json (min=${similarityStats.min.toFixed(3)}, max=${similarityStats.max.toFixed(3)}, ${NUM_BREAKPOINTS} rank breakpoints)`
);
