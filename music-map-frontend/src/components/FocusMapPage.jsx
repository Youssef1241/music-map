import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ArtistGraphCanvas from './ArtistGraphCanvas.jsx';
import LanguageToggle from './LanguageToggle.jsx';
import { useLocale } from './useLocale.js';
import { loadMatrix } from '../loadMatrix';
import t from '../translations.json';

export default function FocusMapPage() {
  const { artistId: artistIdParam } = useParams();
  const artistId = artistIdParam ? Number(artistIdParam) : undefined;
  const navigate = useNavigate();
  const { locale, toggleLocale } = useLocale();
  const [artistName, setArtistName] = useState('');

  useEffect(() => {
    if (!artistId) return;
    loadMatrix().then((m) => {
      setArtistName(
        m.getName(artistId, locale) ||
          m.getName(artistId, locale === 'ar' ? 'en' : 'ar') ||
          ''
      );
    });
  }, [artistId, locale]);


  useEffect(() => {
    if (!artistName) return;
 
    const pageTitle =
      locale === 'ar'
        ? `${artistName} — الفنانين الأقرب له | خريطة الموسيقى العربية`
        : `${artistName} — Similar Artists | Arab Music Map`;
 
    const pageDescription =
      locale === 'ar'
        ? `استكشف أقرب 100 فنان لـ ${artistName} بناءً على تشابه الأغاني في خريطة الموسيقى العربية التفاعلية.`
        : `Explore the 100 artists most similar to ${artistName}, based on song similarity, on the interactive Arab Music Map.`;
 
    document.title = pageTitle;
 
    let metaDesc = document.querySelector('meta[name="description"]');
    if (!metaDesc) {
      metaDesc = document.createElement('meta');
      metaDesc.setAttribute('name', 'description');
      document.head.appendChild(metaDesc);
    }
    metaDesc.setAttribute('content', pageDescription);
 
    // Reset to the site defaults when leaving this page, so the homepage
    // doesn't inherit a stale artist title if the user navigates back.
    return () => {
      document.title = 'خريطة الموسيقى العربية | Arab Music Map';
      metaDesc.setAttribute(
        'content',
        'خريطة تفاعلية لفناني الموسيقى العربية تقيس التشابه بين الفنانين بناءً على أغانيهم. اكتشف فنانين جدد واستكشف العلاقات بين نجوم الموسيقى العربية.'
      );
    };
  }, [artistName, locale]);
 



  return (
    <div className="w-screen h-screen bg-slate-950 text-slate-100 relative overflow-hidden">
      <div className={`absolute top-6 z-10 bg-slate-900/80 border border-slate-700/50 rounded-2xl p-4 shadow-2xl backdrop-blur-md flex flex-col gap-2 ${
        locale === 'ar' ? 'right-6 items-end' : 'left-6 items-start'
      }`}>
        <div className="flex items-center gap-2">
          <LanguageToggle locale={locale} onToggle={toggleLocale} />
          <button onClick={() => navigate('/')} className="px-3 py-1.5 text-xs font-bold bg-slate-950 text-slate-400 rounded-lg hover:text-teal-400 border border-slate-800">
            {t[locale].back}
          </button>
        </div>
        <h2 className="text-sm font-bold text-amber-400">
          {t[locale].artistLabel}{artistName || '...'}
        </h2>
        <p className="text-[10px] text-slate-400">{t[locale].focusMapSub}</p>
      </div>
      <div className="w-full h-full relative z-0">
        <ArtistGraphCanvas
          viewMode="FOCUS"
          focalArtist={artistId}
          locale={locale}
          onNodeClick={(node) => navigate(`/map/${encodeURIComponent(node.id)}`)}
        />
      </div>
    </div>
  );
}