import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { loadMatrix } from '../loadMatrix';
import LanguageToggle from './LanguageToggle.jsx';
import { useLocale } from './useLocale.js';
import t from '../translations.json';

function BackgroundNodes() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const mouse = { x: -1000, y: -1000, radius: 150 };

    const handleMouseMove = (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    const handleMouseLeave = () => {
      mouse.x = -1000;
      mouse.y = -1000;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    const nodes = [];
    const spacing = 90;
    const cols = Math.ceil(window.innerWidth / spacing) + 1;
    const rows = Math.ceil(window.innerHeight / spacing) + 1;

    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        let hue = 0;
        const isAmber = Math.random() < 0.15;
        if (isAmber) {
          hue = 35 + Math.random() * 10;
        } else {
          hue = 180 + Math.random() * 80;
        }
        nodes.push({
          baseX: i * spacing + (Math.random() - 0.5) * 40,
          baseY: j * spacing + (Math.random() - 0.5) * 40,
          x: i * spacing + (Math.random() - 0.5) * 40,
          y: j * spacing + (Math.random() - 0.5) * 40,
          radius: 3.5 + Math.random() * 4,
          vx: (Math.random() - 0.5) * 0.4,
          vy: (Math.random() - 0.5) * 0.4,
          hue: hue,
          phase: Math.random() * Math.PI * 2,
          isAmber: isAmber,
        });
      }
    }

    for (let step = 0; step < 150; step++) {
      const simT = step * 0.015;
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];
        node.x += node.vx + Math.sin(simT + node.phase) * 0.2;
        node.y += node.vy + Math.cos(simT * 0.9 + node.phase) * 0.2;
        node.x += (node.baseX - node.x) * 0.005;
        node.y += (node.baseY - node.y) * 0.005;
      }
    }

    let t = 0;
    const render = () => {
      t += 0.015;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];

        node.x += node.vx + Math.sin(t + node.phase) * 0.2;
        node.y += node.vy + Math.cos(t * 0.9 + node.phase) * 0.2;

        if (node.x < -20) node.x = canvas.width + 20;
        if (node.x > canvas.width + 20) node.x = -20;
        if (node.y < -20) node.y = canvas.height + 20;
        if (node.y > canvas.height + 20) node.y = -20;

        const dx = mouse.x - node.x;
        const dy = mouse.y - node.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        let currentRadius = node.radius;
        let isHovered = false;

        if (dist < mouse.radius) {
          isHovered = true;
          const force = (1 - dist / mouse.radius) * 12;
          const angle = Math.atan2(dy, dx);
          node.x -= Math.cos(angle) * force * 0.15;
          node.y -= Math.sin(angle) * force * 0.15;
          currentRadius += (1 - dist / mouse.radius) * 4;
        }

        if (isHovered) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, currentRadius + 6, 0, Math.PI * 2);
          if (!node.isAmber) {
            ctx.fillStyle = `hsl(${node.hue}, 85%, 52%, 0.25)`;
          } else {
            ctx.fillStyle = `hsl(${node.hue}, 65%, 48%, 0.25)`;
          }
        }

        ctx.beginPath();
        ctx.arc(node.x, node.y, currentRadius, 0, Math.PI * 2);
        if (!node.isAmber) {
          ctx.fillStyle = `hsl(${node.hue}, 85%, 52%)`;
        } else {
          ctx.fillStyle = `hsl(${node.hue}, 65%, 48%)`;
        }

        ctx.fill();

        ctx.beginPath();
        ctx.arc(node.x - currentRadius * 0.3, node.y - currentRadius * 0.3, currentRadius * 0.4, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 pointer-events-auto z-0" />;
}

const normalizeArabic = (text) => {
  return text
    .replace(/[أإآ]/g, 'ا')
    .replace(/ة/g, 'ه')
    .replace(/ى/g, 'ي')
    .toLowerCase();
};



export default function SearchPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredSuggestions, setFilteredSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [matrix, setMatrix] = useState(null);
  const { locale, toggleLocale } = useLocale();

  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadMatrix().then((m) => setMatrix(m));
  }, []);

const [preparedArtists, setPreparedArtists] = useState([]);

useEffect(() => {
  loadMatrix().then((m) => {
    setMatrix(m);
    const rawNames = Array.from(
      new Set(
        m.getAllIds().flatMap((id) => [m.getName(id, 'ar'), m.getName(id, 'en')]).filter(Boolean)
      )
    );
    setPreparedArtists(rawNames.map((a) => ({ original: a, normalized: normalizeArabic(a) })));
  });
}, []);
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredSuggestions([]);
      setShowDropdown(false);
    } else {
      const matches = preparedArtists
        .filter(artist =>
          artist.normalized.includes(normalizeArabic(searchTerm.trim()))
        )
        .slice(0, 10)
        .map(artist => artist.original);

      setFilteredSuggestions(matches);
      setShowDropdown(matches.length > 0);
    }
  }, [searchTerm]);

  const handleSelectArtist = (artistName) => {
    setSearchTerm(artistName);
    setShowDropdown(false);
    
    if (!matrix) return;
    
    const id = matrix.getIdByName(artistName, 'en') ?? matrix.getIdByName(artistName, 'ar');
    if (id !== undefined) {
      navigate(`/map/${id}`);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const trimmed = searchTerm.trim();
    if (trimmed !== '' && matrix) {
      const id = matrix.getIdByName(trimmed, 'en') ?? matrix.getIdByName(trimmed, 'ar');
      if (id !== undefined) {
        setShowDropdown(false);
        navigate(`/map/${id}`);
      } else if (filteredSuggestions.length > 0) {
        handleSelectArtist(filteredSuggestions[0]);
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center justify-between p-6 relative overflow-hidden">
      {/* Background canvas component */}
      <BackgroundNodes />

      {/* Language Switcher Button on top right */}
      <div className="absolute top-6 right-6 z-20">
        <LanguageToggle locale={locale} onToggle={toggleLocale} />
      </div>

      {/* Foreground Container */}
      <div className="relative z-10 flex flex-col items-center justify-center w-full max-w-md pointer-events-none my-auto">
        <div className="text-center mb-8 max-w-md backdrop-blur-sm bg-stone-950/40 p-4 rounded-2xl border border-slate-800/40 shadow-2xl pointer-events-auto">
          <h1
            className="inline-block text-4xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent mb-3"
            style={{ lineHeight: '1.2', paddingBottom: '0.1em' }}
          >
            {t[locale].title}
          </h1>
          <p className="text-amber-400 text-lg">{t[locale].subtitle}</p>
        </div>

        <div className="w-full bg-stone-900 border border-slate-700/50 rounded-2xl p-6 shadow-2xl backdrop-blur-md pointer-events-auto">
          <form onSubmit={handleSearchSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5 relative" ref={dropdownRef}>
              <label className={`text-sm font-medium text-slate-400 block ${locale === 'ar' ? 'text-right' : 'text-left'}`}>
                {t[locale].searchLabel}
              </label>

              <input
                type="text"
                dir="auto"
                placeholder={t[locale].placeholder}
                value={searchTerm}
                onFocus={() => {
                  if (filteredSuggestions.length > 0) setShowDropdown(true);
                }}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={`w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-xl focus:outline-none focus:border-amber-500 text-slate-100 ${
                  locale === 'ar' ? 'placeholder:text-right' : 'placeholder:text-left'
                }`}
              />

              {/* Suggestions Dropdown List */}
              {showDropdown && (
                <ul className="absolute top-full left-0 right-0 mt-2 bg-slate-950/95 border border-slate-700 rounded-xl shadow-2xl max-h-48 overflow-y-auto z-50 backdrop-blur-lg divide-y divide-slate-800/60">
                  {filteredSuggestions.map((artist, index) => (
                    <li
                      key={index}
                      onClick={() => handleSelectArtist(artist)}
                      className={`px-4 py-2.5 hover:bg-slate-800/80 cursor-pointer text-slate-200 hover:text-amber-400 transition-colors ${
                        locale === 'ar' ? 'text-right' : 'text-left'
                      }`}
                      dir="auto"
                    >
                      {artist}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 font-semibold rounded-xl transition-all active:scale-[0.98] hover:bg-gradient-to-r hover:from-emerald-400 hover:to-teal-400"
            >
              {t[locale].searchBtn}
            </button>
          </form>

          <div className="flex items-center gap-3 my-4">
            <div className="h-px flex-1 bg-slate-700/50" />
            <span className="text-xs text-slate-500">{t[locale].or}</span>
            <div className="h-px flex-1 bg-slate-700/50" />
          </div>

          <button
            type="button"
            onClick={() => navigate('/map')}
            className="w-full py-3 bg-slate-950 border border-slate-700 text-slate-300 font-semibold rounded-xl transition-all hover:border-amber-500 hover:text-teal-400 active:scale-[0.98]"
          >
            {t[locale].exploreBtn}
          </button>
        </div>

        {/* How-to-use info card */}
        <div
          className="w-full mt-6 bg-stone-950/40 border border-slate-800/40 rounded-2xl p-5 shadow-xl backdrop-blur-sm pointer-events-auto"
          dir={locale === 'ar' ? 'rtl' : 'ltr'}
        >
          <h2 className={`text-sm font-semibold text-teal-400 mb-3 ${locale === 'ar' ? 'text-right' : 'text-left'}`}>
            {t[locale].howToTitle}
          </h2>
          <ul className="flex flex-col gap-2">
            {t[locale].howToItems.map((item, index) => (
              <li
                key={index}
                className={`text-sm text-slate-300 flex items-start gap-2 ${
                  locale === 'ar' ? 'text-right' : 'text-left'
                }`}
              >
                <span className="text-amber-400 mt-0.5 flex-shrink-0">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Footer Attributions */}
      <footer className="relative z-10 w-full max-w-2xl mt-8 pt-4 pb-2 border-t border-slate-800/60 text-center text-xs text-slate-400 pointer-events-auto backdrop-blur-sm">
        <p className="mb-2">
          Created by{' '}
          <a
            href="https://github.com/Youssef1241"
            target="_blank"
            rel="noopener noreferrer"
            className="text-teal-400 hover:text-amber-400 transition-colors font-medium underline underline-offset-2"
          >
            Youssef Tarek
          </a>
        </p>
        <p className="leading-relaxed text-slate-500">
          Powered by metadata and embeddings from{' '}
          <a href="https://musicbrainz.org/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 underline">MusicBrainz</a>,{' '}
          <a href="https://www.last.fm/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 underline">Last.fm</a>,{' '}
          <a href="https://www.apple.com/itunes/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 underline">iTunes API</a>,{' '}
          <a href="https://query.wikidata.org/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 underline">Wikidata</a>, and{' '}
          <a href="https://www.wikipedia.org/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 underline">Wikipedia</a>.{' '}
          Audio features extracted via <a href="https://essentia.upf.edu/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 underline">Essentia</a> &{' '}
          <a href="https://huggingface.co/m-a-p/MERT-v1-330M" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 underline">MERT-v1-330M</a> (licensed under CC BY-NC 4.0).
          <p className="hover:text-slate-300">
          Icon created by <a href="https://www.flaticon.com/free-icons/vinyl" title="vinyl icons">Vinyl icons created by Magnific - Flaticon</a>
          </p>
        </p>
      </footer>
    </div>
  );
}
