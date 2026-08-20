import React from 'react';

export default function LanguageToggle({ locale, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="px-3 py-1.5 text-xs font-bold bg-slate-950 text-slate-300 rounded-lg border border-slate-800 hover:border-amber-500 hover:text-amber-400 transition-colors"
      aria-label={locale === 'ar' ? 'Switch to English' : 'Switch to Arabic'}
    >
      {locale === 'ar' ? 'English' : 'العربية'}
    </button>
  );
}
