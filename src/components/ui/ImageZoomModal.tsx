'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

interface ImageZoomModalProps {
  src: string;
  alt: string;
  onClose: () => void;
}

const MIN_SCALE = 1;
const MAX_SCALE = 5;

export default function ImageZoomModal({ src, alt, onClose }: ImageZoomModalProps) {
  const { t } = useLanguage();
  const [loaded, setLoaded] = useState(false);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const positionRef = useRef({ x: 0, y: 0 });
  const lastTouchDistRef = useRef(0);
  const lastTapRef = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Keep ref in sync with state for event handlers
  useEffect(() => {
    positionRef.current = position;
  }, [position]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEsc);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  // Reset position when scale returns to 1
  useEffect(() => {
    if (scale <= 1) {
      setPosition({ x: 0, y: 0 });
    }
  }, [scale]);

  // Wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const delta = e.deltaY > 0 ? -0.3 : 0.3;
    setScale(prev => Math.max(MIN_SCALE, Math.min(MAX_SCALE, prev + delta)));
  }, []);

  // Mouse drag for pan
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (scale <= 1) return;
    e.preventDefault();
    setIsDragging(true);
    dragStartRef.current = {
      x: e.clientX - positionRef.current.x,
      y: e.clientY - positionRef.current.y,
    };
  }, [scale]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStartRef.current.x,
      y: e.clientY - dragStartRef.current.y,
    });
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Touch events for pinch zoom and pan
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      // Pinch start
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      lastTouchDistRef.current = dist;
    } else if (e.touches.length === 1 && scale > 1) {
      // Pan start
      setIsDragging(true);
      dragStartRef.current = {
        x: e.touches[0].clientX - positionRef.current.x,
        y: e.touches[0].clientY - positionRef.current.y,
      };
    }
  }, [scale]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      // Pinch move
      e.preventDefault();
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      if (lastTouchDistRef.current > 0) {
        const delta = (dist - lastTouchDistRef.current) * 0.01;
        setScale(prev => Math.max(MIN_SCALE, Math.min(MAX_SCALE, prev + delta)));
      }
      lastTouchDistRef.current = dist;
    } else if (e.touches.length === 1 && isDragging) {
      // Pan move
      setPosition({
        x: e.touches[0].clientX - dragStartRef.current.x,
        y: e.touches[0].clientY - dragStartRef.current.y,
      });
    }
  }, [isDragging]);

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
    lastTouchDistRef.current = 0;
  }, []);

  // Double-click / double-tap to toggle zoom
  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    const now = Date.now();
    if (now - lastTapRef.current < 300) {
      // Double-click
      if (scale > 1) {
        setScale(1);
        setPosition({ x: 0, y: 0 });
      } else {
        setScale(2.5);
      }
      lastTapRef.current = 0;
    } else {
      lastTapRef.current = now;
    }
  }, [scale]);

  const handleZoomIn = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setScale(prev => Math.min(MAX_SCALE, prev + 0.5));
  }, []);

  const handleZoomOut = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setScale(prev => Math.max(MIN_SCALE, prev - 0.5));
  }, []);

  const handleReset = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setScale(1);
    setPosition({ x: 0, y: 0 });
  }, []);

  const handleBackdropClick = useCallback(() => {
    if (scale > 1) {
      // If zoomed, reset first
      setScale(1);
      setPosition({ x: 0, y: 0 });
    } else {
      onClose();
    }
  }, [scale, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/85"
      onClick={handleBackdropClick}
    >
      {/* Top bar */}
      <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-4 py-3 bg-gradient-to-b from-black/60 to-transparent" onClick={(e) => e.stopPropagation()}>
        <span className="text-white/80 text-sm">
          {Math.round(scale * 100)}%
          {scale > 1 && ` — ${t('zoom.hint')}`}
        </span>
        <button
          onClick={onClose}
          className="text-white hover:text-gray-300 p-1"
          aria-label="Close"
        >
          <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Zoom controls */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 bg-black/60 rounded-full px-3 py-2" onClick={(e) => e.stopPropagation()}>
        <button onClick={handleZoomOut} disabled={scale <= MIN_SCALE} className="text-white hover:text-gray-300 disabled:text-gray-600 p-1.5" aria-label="Zoom out">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
        <button onClick={handleReset} className="text-white hover:text-gray-300 text-xs px-2 py-1 rounded" aria-label="Reset zoom">
          {Math.round(scale * 100)}%
        </button>
        <button onClick={handleZoomIn} disabled={scale >= MAX_SCALE} className="text-white hover:text-gray-300 disabled:text-gray-600 p-1.5" aria-label="Zoom in">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      {/* Loading indicator */}
      {!loaded && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-white z-10">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white mb-3"></div>
          <p className="text-sm text-gray-300">{t('zoom.loading')}</p>
        </div>
      )}

      {/* Image container */}
      <div
        ref={containerRef}
        className={`max-w-full max-h-full overflow-hidden ${
          scale > 1 ? (isDragging ? 'cursor-grabbing' : 'cursor-grab') : 'cursor-zoom-in'
        }`}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onClick={handleClick}
        style={{ touchAction: 'none' }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src}
          alt={alt}
          onLoad={() => setLoaded(true)}
          className={`max-w-[90vw] max-h-[85vh] object-contain transition-opacity duration-300 select-none ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            transition: isDragging ? 'none' : 'transform 0.15s ease-out',
          }}
          draggable={false}
        />
      </div>
    </div>
  );
}
