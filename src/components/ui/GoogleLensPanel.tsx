'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { LENS_CONFIG } from '@/lib/experimentConfig';
import type { LensResult } from '@/types';

interface GoogleLensPanelProps {
  imageSrc: string;
  results: LensResult[];
  onClose: () => void;
  onResultClick: (index: number, result: LensResult) => void;
  onScroll: () => void;
}

export default function GoogleLensPanel({
  imageSrc,
  results,
  onClose,
  onResultClick,
  onScroll,
}: GoogleLensPanelProps) {
  const { t } = useLanguage();
  const [showBlockedDialog, setShowBlockedDialog] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const hasLoggedScroll = useRef(false);

  const handleScroll = useCallback(() => {
    if (!hasLoggedScroll.current && scrollRef.current) {
      if (scrollRef.current.scrollTop > LENS_CONFIG.scrollLogThreshold) {
        hasLoggedScroll.current = true;
        onScroll();
      }
    }
  }, [onScroll]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (showBlockedDialog) {
          setShowBlockedDialog(false);
        } else {
          onClose();
        }
      }
    };
    document.addEventListener('keydown', handleEsc);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = '';
    };
  }, [onClose, showBlockedDialog]);

  const handleResultClick = (index: number, result: LensResult) => {
    onResultClick(index, result);
    setShowBlockedDialog(true);
  };

  const { thumbnail, sourcePreview, layout, gridColumns } = LENS_CONFIG;
  const isGrid = layout === 'grid';

  return (
    <div className="fixed inset-0 z-[90] flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Panel - use CSS classes for responsive sizing, config values as defaults */}
      <div
        className={`relative z-10 bg-[#F1F3F4] w-full sm:max-w-[90vw] sm:rounded-xl rounded-t-xl flex flex-col overflow-hidden shadow-2xl`}
        style={{
          maxHeight: `${LENS_CONFIG.panelMaxHeightMobile}vh`,
        }}
      >
        <style>{`
          @media (min-width: 640px) {
            .lens-panel-responsive {
              width: ${LENS_CONFIG.panelWidth}px !important;
              max-height: ${LENS_CONFIG.panelMaxHeightDesktop}vh !important;
            }
          }
        `}</style>
        <div className="lens-panel-responsive contents sm:!contents" />

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shrink-0">
          <div className="flex items-center gap-2">
            <LensLogo className="w-5 h-5" />
            <span className="font-medium text-gray-800 text-sm">Google Lens</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Source image preview */}
        <div className="px-4 py-3 bg-white border-b border-gray-200 shrink-0">
          <div className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={imageSrc}
              alt="Search image"
              className="object-cover rounded-lg border border-gray-200"
              style={{ width: sourcePreview.width, height: sourcePreview.height }}
            />
            <div>
              <p className="text-xs text-gray-500">{t('lens.matchesFound')}</p>
              <p className="text-sm font-medium text-gray-700">
                {t('lens.visualMatches').replace('{count}', String(results.length))}
              </p>
            </div>
          </div>
        </div>

        {/* Results */}
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className={`flex-1 overflow-y-auto px-3 py-3 ${
            isGrid ? 'grid gap-2' : 'space-y-2'
          }`}
          style={isGrid ? { gridTemplateColumns: `repeat(${gridColumns}, 1fr)` } : undefined}
        >
          {results.map((result, idx) =>
            isGrid ? (
              <button
                key={idx}
                onClick={() => handleResultClick(idx, result)}
                className="bg-white rounded-lg border border-gray-200 p-2 flex flex-col items-center gap-2 hover:shadow-md transition-shadow text-center cursor-pointer"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={result.thumbnailUrl}
                  alt=""
                  className="object-cover rounded-md bg-gray-100"
                  style={{ width: thumbnail.width, height: thumbnail.height }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
                <p className="text-xs font-medium text-gray-900 line-clamp-2">{result.title}</p>
                <p className="text-xs text-green-700 truncate w-full">{result.source}</p>
              </button>
            ) : (
              <button
                key={idx}
                onClick={() => handleResultClick(idx, result)}
                className="w-full bg-white rounded-lg border border-gray-200 p-3 flex items-start gap-3 hover:shadow-md transition-shadow text-left cursor-pointer"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={result.thumbnailUrl}
                  alt=""
                  className="object-cover rounded-md flex-shrink-0 bg-gray-100"
                  style={{ width: thumbnail.width, height: thumbnail.height }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 line-clamp-2">{result.title}</p>
                  <p className="text-xs text-green-700 mt-1 truncate">{result.source}</p>
                  {result.snippet && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{result.snippet}</p>
                  )}
                </div>
              </button>
            )
          )}
        </div>
      </div>

      {/* Blocked Navigation Dialog */}
      {showBlockedDialog && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/30" onClick={() => setShowBlockedDialog(false)} />
          <div className="relative bg-white rounded-xl shadow-2xl p-6 max-w-sm mx-4 text-center">
            <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m0 0v2m0-2h2m-2 0H10m4-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {t('lens.blockedTitle')}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              {t('lens.blockedMessage')}
            </p>
            <button
              onClick={() => setShowBlockedDialog(false)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              {t('lens.blockedOk')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function LensLogo({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="5" stroke="#4285F4" strokeWidth="2" fill="none" />
      <path d="M12 2v5" stroke="#EA4335" strokeWidth="2" strokeLinecap="round" />
      <path d="M12 17v5" stroke="#34A853" strokeWidth="2" strokeLinecap="round" />
      <path d="M2 12h5" stroke="#FBBC05" strokeWidth="2" strokeLinecap="round" />
      <path d="M17 12h5" stroke="#4285F4" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
