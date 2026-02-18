'use client';

import { useEffect, useRef } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

interface FakeContextMenuProps {
  x: number;
  y: number;
  onSearchImage: () => void;
  onClose: () => void;
}

export default function FakeContextMenu({ x, y, onSearchImage, onClose }: FakeContextMenuProps) {
  const { t } = useLanguage();
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on click outside or ESC
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside as unknown as EventListener);
      document.addEventListener('keydown', handleEsc);
    }, 50);
    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside as unknown as EventListener);
      document.removeEventListener('keydown', handleEsc);
    };
  }, [onClose]);

  // Adjust position to keep menu within viewport
  useEffect(() => {
    if (!menuRef.current) return;
    const el = menuRef.current;
    const rect = el.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
      el.style.left = `${Math.max(4, x - rect.width)}px`;
    }
    if (rect.bottom > window.innerHeight) {
      el.style.top = `${Math.max(4, y - rect.height)}px`;
    }
  }, [x, y]);

  const menuItems = [
    { label: t('contextMenu.openImageNewTab'), disabled: true },
    { label: t('contextMenu.saveImageAs'), disabled: true },
    { label: t('contextMenu.copyImage'), disabled: true },
    { type: 'separator' as const },
    {
      label: t('contextMenu.searchImageWithGoogle'),
      icon: 'lens' as const,
      onClick: onSearchImage,
    },
  ];

  return (
    <div
      ref={menuRef}
      className="fixed z-[100] bg-white rounded-lg shadow-xl border border-gray-200 py-1 min-w-[260px] text-sm select-none"
      style={{ left: x, top: y }}
    >
      {menuItems.map((item, idx) => {
        if (item.type === 'separator') {
          return <div key={idx} className="border-t border-gray-200 my-1" />;
        }
        return (
          <button
            key={idx}
            onClick={(e) => {
              e.stopPropagation();
              item.onClick?.();
            }}
            disabled={item.disabled}
            className={`w-full text-left px-3 py-2 flex items-center gap-2.5 ${
              item.disabled
                ? 'text-gray-400 cursor-default'
                : 'text-gray-700 hover:bg-blue-50 cursor-pointer'
            }`}
          >
            {item.icon === 'lens' && <LensIcon className="w-4 h-4 flex-shrink-0" />}
            <span>{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}

function LensIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="5.5" stroke="#4285F4" strokeWidth="2" fill="none" />
      <path d="M12 2v4.5" stroke="#EA4335" strokeWidth="2" strokeLinecap="round" />
      <path d="M12 17.5V22" stroke="#34A853" strokeWidth="2" strokeLinecap="round" />
      <path d="M2 12h4.5" stroke="#FBBC05" strokeWidth="2" strokeLinecap="round" />
      <path d="M17.5 12H22" stroke="#4285F4" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
