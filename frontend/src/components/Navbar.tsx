'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { getStatus } from '@/lib/api';
import type { StatusResponse } from '@/types';

export default function Navbar() {
  const [status, setStatus] = useState<StatusResponse | null>(null);

  useEffect(() => {
    getStatus().then(setStatus).catch(() => setStatus({ mode: 'demo', live_ai_available: false, provider: null, demo_available: true }));
    const interval = setInterval(() => {
      getStatus().then(setStatus).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const isLive = status?.mode === 'live';

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-panel border-0 border-b border-[var(--border)]" style={{ borderRadius: 0 }}>
      <div className="max-w-[1800px] mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white font-bold text-sm">SQ</div>
            <span className="font-bold text-base tracking-tight text-white">SATQUERY <span className="text-blue-400">AI</span></span>
          </Link>
          <div className="hidden md:flex items-center gap-1">
            {[
              { href: '/', label: 'Overview' },
              { href: '/analyze', label: 'Analyze' },
              { href: '/compare', label: 'Compare' },
              { href: '/history', label: 'History' },
            ].map(link => (
              <Link key={link.href} href={link.href}
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-md transition-colors">
                {link.label}
              </Link>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
            style={{ background: isLive ? 'rgba(34,197,94,0.1)' : 'rgba(59,130,246,0.1)', border: `1px solid ${isLive ? 'rgba(34,197,94,0.3)' : 'rgba(59,130,246,0.3)'}` }}>
            <span className={`w-2 h-2 rounded-full pulse-dot ${isLive ? 'bg-green-400' : 'bg-blue-400'}`}></span>
            <span className={isLive ? 'text-green-400' : 'text-blue-400'}>
              {isLive ? 'LIVE AI' : 'DEMO MODE'}
            </span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-green-500/10 border border-green-500/30">
            <span className="w-2 h-2 rounded-full bg-green-400 pulse-dot"></span>
            <span className="text-green-400">API CONNECTED</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
