// scripts/generate-sitemap.mjs
//
// Generates public/sitemap.xml from public/data/artist-index.json.
// Run manually with `node scripts/generate-sitemap.mjs`, or wire it into
// your build (see instructions below).

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '..');

const SITE_URL = 'https://www.arabmusicmap.wiki';
const ARTIST_INDEX_PATH = path.join(PROJECT_ROOT, 'public', 'data', 'artist-index.json');
const OUTPUT_PATH = path.join(PROJECT_ROOT, 'public', 'sitemap.xml');

function xmlEscape(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function urlEntry(loc, { changefreq, priority } = {}) {
  return [
    '  <url>',
    `    <loc>${xmlEscape(loc)}</loc>`,
    changefreq ? `    <changefreq>${changefreq}</changefreq>` : null,
    priority != null ? `    <priority>${priority}</priority>` : null,
    '  </url>',
  ]
    .filter(Boolean)
    .join('\n');
}

function main() {
  if (!existsSync(ARTIST_INDEX_PATH)) {
    console.error(`Could not find artist-index.json at: ${ARTIST_INDEX_PATH}`);
    console.error('Update ARTIST_INDEX_PATH at the top of this script if your file lives elsewhere.');
    process.exit(1);
  }

  const raw = readFileSync(ARTIST_INDEX_PATH, 'utf-8');
  const artistIndex = JSON.parse(raw);

  // Supports two shapes:
  //   { "123": { name: "...", name_en: "..." } }   -> uses the object key as the id
  //   { "123": { id: "123", name: "...", ... } }    -> uses the `id` field if present
  const entries = Object.entries(artistIndex).map(([key, artist]) => {
    const id = artist && artist.id != null ? artist.id : key;
    return { id, name: artist?.name, name_en: artist?.name_en };
  });

  const seenIds = new Set();
  const urls = [];

  // Static routes
  urls.push(urlEntry(`${SITE_URL}/`, { changefreq: 'weekly', priority: '1.0' }));
  urls.push(urlEntry(`${SITE_URL}/map`, { changefreq: 'weekly', priority: '0.8' }));

  // One URL per artist focus page
  for (const { id } of entries) {
    if (id == null || seenIds.has(id)) continue;
    seenIds.add(id);
    urls.push(
      urlEntry(`${SITE_URL}/map/${encodeURIComponent(id)}`, {
        changefreq: 'monthly',
        priority: '0.6',
      })
    );
  }

  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    urls.join('\n'),
    '</urlset>',
    '',
  ].join('\n');

  writeFileSync(OUTPUT_PATH, xml, 'utf-8');
  console.log(`Wrote ${seenIds.size} artist URLs (+ 2 static routes) to ${OUTPUT_PATH}`);
}

main();
