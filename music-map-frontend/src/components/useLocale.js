import { useState, useEffect } from 'react';

const LOCALE_KEY = 'music-map-locale';

export function useLocale() {
  const [locale, setLocale] = useState(() =>
    localStorage.getItem(LOCALE_KEY) === 'en' ? 'en' : 'ar'
  );

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr';
  }, [locale]);

  const toggleLocale = () => {
    setLocale((prev) => {
      const next = prev === 'ar' ? 'en' : 'ar';
      localStorage.setItem(LOCALE_KEY, next);
      return next;
    });
  };

  return { locale, toggleLocale, setLocale };
}