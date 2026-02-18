'use client';

import { useState, useRef, useCallback } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useInteractionLogger } from '@/hooks/useInteractionLogger';
import { getLensData } from '@/lib/lensData';
import ImageZoomModal from '@/components/ui/ImageZoomModal';
import FakeContextMenu from '@/components/ui/FakeContextMenu';
import GoogleLensPanel from '@/components/ui/GoogleLensPanel';

interface ImageDisplayProps {
  thumbSrc: string;
  fullSrc: string;
  alt: string;
  imageId: string;
  imageOrder: number;
  participantId: string | null;
  onLoad: () => void;
}

export default function ImageDisplay({
  thumbSrc,
  fullSrc,
  alt,
  imageId,
  imageOrder,
  participantId,
  onLoad,
}: ImageDisplayProps) {
  const { t } = useLanguage();
  const { logInteraction } = useInteractionLogger({ participantId, imageId, imageOrder });

  const [zoomed, setZoomed] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // Context menu state
  const [menuPos, setMenuPos] = useState<{ x: number; y: number } | null>(null);
  // Lens panel state
  const [showLens, setShowLens] = useState(false);

  // Long-press detection refs
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const touchStartPos = useRef<{ x: number; y: number } | null>(null);
  const didLongPress = useRef(false);

  const handleLoad = () => {
    setLoaded(true);
    onLoad();
  };

  // === PC: Right-click ===
  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setMenuPos({ x: e.clientX, y: e.clientY });
      logInteraction('TRIGGER_MENU');
    },
    [logInteraction]
  );

  // === Mobile: Long-press (600ms) ===
  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      const touch = e.touches[0];
      touchStartPos.current = { x: touch.clientX, y: touch.clientY };
      didLongPress.current = false;

      longPressTimer.current = setTimeout(() => {
        didLongPress.current = true;
        setMenuPos({ x: touch.clientX, y: touch.clientY });
        logInteraction('TRIGGER_MENU');
      }, 600);
    },
    [logInteraction]
  );

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!touchStartPos.current || !longPressTimer.current) return;
    const touch = e.touches[0];
    const dx = touch.clientX - touchStartPos.current.x;
    const dy = touch.clientY - touchStartPos.current.y;
    // Cancel long press if finger moves > 10px
    if (Math.sqrt(dx * dx + dy * dy) > 10) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }, []);

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
    // If long-press fired, prevent the subsequent click (zoom)
    if (didLongPress.current) {
      e.preventDefault();
      didLongPress.current = false;
    }
  }, []);

  // === Context menu → Search image ===
  const handleSearchImage = useCallback(() => {
    setMenuPos(null);
    setShowLens(true);
    logInteraction('OPEN_LENS');
  }, [logInteraction]);

  const handleCloseMenu = useCallback(() => {
    setMenuPos(null);
  }, []);

  // === Lens panel callbacks ===
  const handleCloseLens = useCallback(() => {
    setShowLens(false);
  }, []);

  const handleLensResultClick = useCallback(
    (index: number, result: { title: string }) => {
      logInteraction('CLICK_RESULT', { result_index: index, result_title: result.title });
    },
    [logInteraction]
  );

  const handleLensScroll = useCallback(() => {
    logInteraction('SCROLL_LENS');
  }, [logInteraction]);

  const lensData = getLensData(imageId);

  return (
    <>
      <div
        className="relative bg-gray-100 rounded-lg overflow-hidden mb-6 flex items-center justify-center"
        style={{ minHeight: '200px', maxHeight: '500px' }}
        onContextMenu={handleContextMenu}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {!loaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 animate-pulse">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={thumbSrc}
          alt={alt}
          onLoad={handleLoad}
          onClick={() => setZoomed(true)}
          className={`max-w-full max-h-[500px] object-contain cursor-zoom-in transition-opacity duration-300 ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
          draggable={false}
        />
        {loaded && (
          <button
            onClick={() => setZoomed(true)}
            className="absolute bottom-3 right-3 bg-white/80 hover:bg-white text-gray-700 px-3 py-2 rounded-md text-sm flex items-center gap-1.5 shadow-sm min-w-[48px] min-h-[48px]"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
            <span className="hidden sm:inline">{t('image.zoomFull')}</span>
            <span className="sm:hidden">{t('image.zoom')}</span>
          </button>
        )}
      </div>

      {/* Zoom modal */}
      {zoomed && (
        <ImageZoomModal src={fullSrc} alt={alt} onClose={() => setZoomed(false)} />
      )}

      {/* Fake context menu */}
      {menuPos && (
        <FakeContextMenu
          x={menuPos.x}
          y={menuPos.y}
          onSearchImage={handleSearchImage}
          onClose={handleCloseMenu}
        />
      )}

      {/* Google Lens panel */}
      {showLens && (
        <GoogleLensPanel
          imageSrc={thumbSrc}
          results={lensData.results}
          onClose={handleCloseLens}
          onResultClick={handleLensResultClick}
          onScroll={handleLensScroll}
        />
      )}
    </>
  );
}
