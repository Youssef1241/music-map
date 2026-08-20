// src/data/loadMatrix.js
//
// Loads artist-index.json + similarity-matrix.bin (produced by build-matrix.mjs)
// and exposes fast, name-based lookups backed by a single dense Float32Array.
//
// Usage:
//   const matrix = await loadMatrix();
//   matrix.getSimilarity('Fairuz', 'Amr Diab');   // -> number
//   matrix.getFullRow('Fairuz');                  // -> [{ name, similarity }, ...] sorted desc
//   matrix.getPopularity('Fairuz');                // -> number
//   matrix.getAllNames();                          // -> string[]

let cached = null;

export async function loadMatrix({
  indexUrl = '/data/artist-index.json',
  matrixUrl = '/data/similarity-matrix.bin',
  statsUrl = '/data/similarity-stats.json',
} = {}) {
  if (cached) return cached;

  const [indexRes, matrixRes, statsRes] = await Promise.all([
    fetch(indexUrl),
    fetch(matrixUrl),
    fetch(statsUrl),
  ]);

  if (!indexRes.ok) throw new Error(`Failed to load ${indexUrl}: ${indexRes.status}`);
  if (!matrixRes.ok) throw new Error(`Failed to load ${matrixUrl}: ${matrixRes.status}`);
  if (!statsRes.ok) throw new Error(`Failed to load ${statsUrl}: ${statsRes.status}`);

  const index = await indexRes.json(); // [{ id, name, popularity }, ...] in row order
  const buffer = await matrixRes.arrayBuffer();

  const n = index.length;
  const matrix = new Float32Array(buffer); // zero-copy view, length must be n*n
  const stats = await statsRes.json();

  if (matrix.length !== n * n) {
    throw new Error(
      `Matrix size mismatch: expected ${n * n} floats for ${n} artists, got ${matrix.length}`
    );
  }

  // name -> row index, and row index -> name/popularity, built once
  const idToRow = new Map(); 
  const nameToIdAr = new Map();
  const nameToIdEn = new Map();
  const rowToId = new Array(n); 
  const names = new Array(n);
  const popularity = new Float32Array(n);
  let maxPopularity = 0;

  index.forEach((entry, i) => {
    idToRow.set(entry.id, i);
    rowToId[i] = entry.id;
    names[i] = {ar: entry.name, en: entry.name_en};
    popularity[i] = entry.popularity;
    if (entry.popularity > maxPopularity) maxPopularity = entry.popularity;
    if (entry.name) nameToIdAr.set(entry.name, entry.id);
    if (entry.name_en) nameToIdEn.set(entry.name_en, entry.id);
  });

  function normalizeId(id) {
    if (typeof id === 'string' && id !== '' && !Number.isNaN(Number(id))) {
      return Number(id);
    }
    return id;
  }

  function rowOf(id) {
    const i = idToRow.get(normalizeId(id));
    if (i === undefined) throw new Error(`Unknown artist id: ${id}`);
    return i;
  }

  cached = {

    getSimilarityPercentile(value) {
    const bp = stats.breakpoints;
    let lo = 0, hi = bp.length - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (bp[mid] < value) lo = mid + 1;
      else hi = mid;
    }
    return Math.round((lo / bp.length) * 100);
    },

    getIdByName(name, locale = 'ar') {
    return (locale === 'en' ? nameToIdEn : nameToIdAr).get(name);
    },


    getName(id, locale = 'ar') {
    const i = rowOf(id);
    return names[i][locale];
    },

    // Raw similarity between two artists — O(1), no scanning
    getSimilarity(idA, idB) {
      const i = rowOf(idA);
      const j = rowOf(idB);
      return matrix[i * n + j];
    },


    // Full similarity row for one artist, as sorted [{ name, similarity }]
    // Uses subarray (a view, no copy) before mapping to objects.
    getFullRow(id) {
      const i = rowOf(id);
      const row = matrix.subarray(i * n, i * n + n);

      const result = [];
      for (let j = 0; j < n; j++) {
        if (j === i) continue;
        const sim = row[j];
        if (sim > 0) result.push({ id: rowToId[j], similarity: sim });
      }
      result.sort((a, b) => b.similarity - a.similarity);
      return result;
    },

    getPopularity(id) {
      return popularity[rowOf(id)];
    },

    getMaxPopularity() {
      return maxPopularity;
    },

    getAllIds() {
      return rowToId;
    },

    // Escape hatch if you need the top-2-per-artist GLOBAL view without
    // building it as a separate precomputed file — still O(1) per row since
    // getFullRow no longer scans the whole dataset, just this one row.
    getTopN(id, count) {
      return this.getFullRow(id).slice(0, count);
    },
  };

  return cached;
}