'use client';
import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { getHistory } from '@/lib/api';
import type { HistoryEntry } from '@/types';

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory()
      .then(d => setEntries(d.entries))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Navbar />
      <main className="pt-16 min-h-screen">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <h1 className="text-2xl font-bold text-white mb-2">Analysis History</h1>
          <p className="text-sm text-gray-500 mb-8">Recent satellite image analyses</p>

          {loading ? (
            <div className="text-center py-20 text-gray-500">Loading...</div>
          ) : entries.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-4xl mb-4">📋</div>
              <p className="text-gray-500">No analyses yet. Go to Analyze or Compare to get started.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {entries.map(entry => (
                <div key={entry.id} className="glass-panel p-4 hover:border-blue-500/30 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="text-sm font-medium text-white truncate">{entry.query}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded shrink-0 ${
                          entry.mode === 'live' ? 'bg-green-500/10 text-green-400 border border-green-500/30' : 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                        }`}>
                          {entry.mode === 'live' ? 'LIVE' : 'DEMO'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 line-clamp-2">{entry.answer}</p>
                      <div className="flex items-center gap-4 mt-2 text-[10px] text-gray-500">
                        <span>📷 {entry.image_name}</span>
                        <span>🎯 {entry.intent.replace(/_/g, ' ')}</span>
                        <span>📊 {(entry.confidence * 100).toFixed(0)}%</span>
                        <span>🕐 {new Date(entry.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
