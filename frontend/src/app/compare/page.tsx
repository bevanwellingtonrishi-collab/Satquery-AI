'use client';
import { useState, useRef, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { compareImages, getDemoImageUrl, generateReport, followUp } from '@/lib/api';
import type { CompareResponse, ChatMessage, AnalysisResponse } from '@/types';

export default function ComparePage() {
  const [beforeFile, setBeforeFile] = useState<File | null>(null);
  const [afterFile, setAfterFile] = useState<File | null>(null);
  const [beforeUrl, setBeforeUrl] = useState('');
  const [afterUrl, setAfterUrl] = useState('');
  const [query, setQuery] = useState('What has changed between these two images?');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState('');
  const [sliderPos, setSliderPos] = useState(50);
  const [dragging, setDragging] = useState(false);
  const sliderRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const beforeInputRef = useRef<HTMLInputElement>(null);
  const afterInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadDemo = async () => {
    const beforeUrl = getDemoImageUrl('urban_2023');
    const afterUrl = getDemoImageUrl('urban_2026');
    setBeforeUrl(beforeUrl);
    setAfterUrl(afterUrl);
    try {
      const [bRes, aRes] = await Promise.all([fetch(beforeUrl), fetch(afterUrl)]);
      const [bBlob, aBlob] = await Promise.all([bRes.blob(), aRes.blob()]);
      setBeforeFile(new File([bBlob], 'urban_2023.png', { type: 'image/png' }));
      setAfterFile(new File([aBlob], 'urban_2026.png', { type: 'image/png' }));
    } catch (e) { console.error(e); }
  };

  const loadFloodDemo = async () => {
    const beforeUrl = getDemoImageUrl('flood_before');
    const afterUrl = getDemoImageUrl('flood_after');
    setBeforeUrl(beforeUrl);
    setAfterUrl(afterUrl);
    try {
      const [bRes, aRes] = await Promise.all([fetch(beforeUrl), fetch(afterUrl)]);
      const [bBlob, aBlob] = await Promise.all([bRes.blob(), aRes.blob()]);
      setBeforeFile(new File([bBlob], 'flood_before.png', { type: 'image/png' }));
      setAfterFile(new File([aBlob], 'flood_after.png', { type: 'image/png' }));
    } catch (e) { console.error(e); }
  };

  const handleFile = (which: 'before' | 'after', file: File) => {
    const url = URL.createObjectURL(file);
    if (which === 'before') { setBeforeFile(file); setBeforeUrl(url); }
    else { setAfterFile(file); setAfterUrl(url); }
    setResult(null);
    setMessages([]);
    setSessionId('');
  };

  const handleCompare = async () => {
    if (!beforeFile || !afterFile || !query.trim()) return;
    setLoading(true);
    const userMsg: ChatMessage = { role: 'user', content: query, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);

    try {
      const res = await compareImages(beforeFile, afterFile, query, sessionId);
      if (!sessionId) setSessionId(res.session_id);
      setResult(res);

      const summary = `Detected ${res.changes.length} changes with ${(res.overall_change * 100).toFixed(0)}% overall change magnitude. ` +
        res.changes.map(c => `${c.type.replace(/_/g, ' ')} (${c.severity} severity)`).join(', ') + '.';

      const aiMsg: ChatMessage = { role: 'assistant', content: summary, timestamp: Date.now(), analysis: res };
      setMessages(prev => [...prev, aiMsg]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}`, timestamp: Date.now() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFollowUp = async () => {
    if (!query.trim() || !sessionId) return;
    setLoading(true);
    const userMsg: ChatMessage = { role: 'user', content: query, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    const q = query;
    setQuery('');

    try {
      const res = await followUp(q, sessionId);
      const aiMsg: ChatMessage = { role: 'assistant', content: res.answer, timestamp: Date.now(), analysis: res };
      setMessages(prev => [...prev, aiMsg]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}`, timestamp: Date.now() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    if (result && sessionId) handleFollowUp();
    else handleCompare();
  };

  const handleReport = async () => {
    if (!result) return;
    try {
      const blob = await generateReport(
        messages.find(m => m.role === 'user')?.content || 'Comparison',
        { ...result, answer: `Comparison: ${result.changes.length} changes detected.` },
        `${beforeFile?.name || 'before'} vs ${afterFile?.name || 'after'}`,
        result.heatmap_base64,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'satquery_comparison_report.pdf';
      a.click();
    } catch (e) { console.error(e); }
  };

  const handleSliderMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (!dragging || !sliderRef.current) return;
    const rect = sliderRef.current.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const pos = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
    setSliderPos(pos);
  };

  return (
    <>
      <Navbar />
      <main className="pt-16 min-h-screen">
        <div className="max-w-[1800px] mx-auto px-4 py-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-white">Before &amp; After Comparison</h1>
              <p className="text-sm text-gray-500">Upload two satellite images to detect changes</p>
            </div>
            <div className="flex gap-2">
              <button onClick={loadDemo} className="btn-secondary text-sm">🏙️ Urban Demo (2023 vs 2026)</button>
              <button onClick={loadFloodDemo} className="btn-secondary text-sm">🌊 Flood Demo</button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4" style={{ minHeight: 'calc(100vh - 160px)' }}>
            {/* Left: Image upload + slider */}
            <div className="lg:col-span-8 flex flex-col gap-4">
              {/* Upload row */}
              {(!beforeFile || !afterFile) && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="glass-panel p-4">
                    <h3 className="text-sm font-semibold text-gray-300 mb-2">BEFORE Image</h3>
                    <div className="border-2 border-dashed border-gray-700 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500/50 transition-colors"
                      onClick={() => beforeInputRef.current?.click()}
                      onDrop={e => { e.preventDefault(); handleFile('before', e.dataTransfer.files[0]); }}
                      onDragOver={e => e.preventDefault()}>
                      <input ref={beforeInputRef} type="file" accept="image/*,.tif,.tiff" className="hidden"
                        onChange={e => e.target.files?.[0] && handleFile('before', e.target.files[0])} />
                      {beforeUrl ? (
                        <img src={beforeUrl} alt="Before" className="max-h-32 mx-auto rounded" />
                      ) : (
                        <><div className="text-2xl mb-2">📅</div><p className="text-xs text-gray-400">Drop BEFORE image</p></>
                      )}
                    </div>
                  </div>
                  <div className="glass-panel p-4">
                    <h3 className="text-sm font-semibold text-gray-300 mb-2">AFTER Image</h3>
                    <div className="border-2 border-dashed border-gray-700 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500/50 transition-colors"
                      onClick={() => afterInputRef.current?.click()}
                      onDrop={e => { e.preventDefault(); handleFile('after', e.dataTransfer.files[0]); }}
                      onDragOver={e => e.preventDefault()}>
                      <input ref={afterInputRef} type="file" accept="image/*,.tif,.tiff" className="hidden"
                        onChange={e => e.target.files?.[0] && handleFile('after', e.target.files[0])} />
                      {afterUrl ? (
                        <img src={afterUrl} alt="After" className="max-h-32 mx-auto rounded" />
                      ) : (
                        <><div className="text-2xl mb-2">📅</div><p className="text-xs text-gray-400">Drop AFTER image</p></>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Comparison Slider */}
              {beforeUrl && afterUrl && (
                <div className="glass-panel p-4 fade-in">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-gray-300">Interactive Comparison</h3>
                    <div className="flex gap-2 text-xs">
                      <span className="text-gray-500">◀ Before</span>
                      <span className="text-gray-500">After ▶</span>
                    </div>
                  </div>
                  <div ref={sliderRef} className="relative h-[400px] rounded-lg overflow-hidden cursor-col-resize select-none"
                    onMouseDown={() => setDragging(true)}
                    onMouseUp={() => setDragging(false)}
                    onMouseLeave={() => setDragging(false)}
                    onMouseMove={handleSliderMove}
                    onTouchStart={() => setDragging(true)}
                    onTouchEnd={() => setDragging(false)}
                    onTouchMove={handleSliderMove}>
                    {/* After (full) */}
                    <img src={afterUrl} alt="After" className="absolute inset-0 w-full h-full object-cover" />
                    {/* Before (clipped) */}
                    <div className="absolute inset-0 overflow-hidden" style={{ width: `${sliderPos}%` }}>
                      <img src={beforeUrl} alt="Before" className="absolute inset-0 w-full h-full object-cover"
                        style={{ width: `${sliderRef.current?.offsetWidth || 800}px` }} />
                    </div>
                    {/* Slider line */}
                    <div className="absolute top-0 bottom-0 w-1 bg-white/80 shadow-lg" style={{ left: `${sliderPos}%`, transform: 'translateX(-50%)' }}>
                      <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-white shadow-lg flex items-center justify-center text-gray-800 text-xs font-bold">⇔</div>
                    </div>
                    {/* Labels */}
                    <div className="absolute top-3 left-3 bg-black/60 text-white text-xs px-2 py-1 rounded">BEFORE</div>
                    <div className="absolute top-3 right-3 bg-black/60 text-white text-xs px-2 py-1 rounded">AFTER</div>
                  </div>
                </div>
              )}

              {/* Heatmap */}
              {result?.heatmap_base64 && (
                <div className="glass-panel p-4 fade-in">
                  <h3 className="text-sm font-semibold text-gray-300 mb-1">Visual Change Map</h3>
                  <p className="text-[10px] text-gray-500 mb-3">Pixel-difference visualization — AI-assisted visual aid, not scientific change detection</p>
                  <img src={`data:image/png;base64,${result.heatmap_base64}`} alt="Change heatmap" className="w-full rounded-lg" />
                </div>
              )}

              {/* Change Details */}
              {result && result.changes.length > 0 && (
                <div className="glass-panel p-4 fade-in">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-gray-300">Detected Changes</h3>
                    <span className="text-xs px-2 py-1 rounded bg-blue-600/20 text-blue-400">
                      Overall: {(result.overall_change * 100).toFixed(0)}% change
                    </span>
                  </div>
                  <div className="space-y-3">
                    {result.changes.map((c, i) => (
                      <div key={i} className="border border-gray-800 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-200">{c.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] px-2 py-0.5 rounded font-bold priority-${c.severity}`}>{c.severity.toUpperCase()}</span>
                            <span className="text-xs text-gray-500">{(c.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                        <p className="text-xs text-gray-400">{c.description}</p>
                        <p className="text-[10px] text-gray-500 mt-1">{c.evidence_description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Evidence Findings */}
              {result && result.findings.length > 0 && (
                <div className="glass-panel p-4 fade-in">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">Evidence-Based Findings</h3>
                  <div className="space-y-3">
                    {result.findings.map((f, i) => (
                      <div key={i} className="border border-gray-800 rounded-lg p-3">
                        <div className="flex items-start justify-between mb-1">
                          <span className="text-sm text-gray-200 font-medium">{f.finding}</span>
                          <span className="text-xs px-2 py-0.5 rounded bg-blue-600/20 text-blue-400 ml-2 shrink-0">{(f.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <p className="text-xs text-gray-400">{f.evidence_description}</p>
                        <div className="flex items-center gap-3 text-[10px] mt-1">
                          <span className="text-gray-500">Quality: <span className="capitalize text-gray-400">{f.evidence_quality}</span></span>
                          {f.region && <span className="text-blue-500">📍 AI-estimated region</span>}
                        </div>
                        {f.limitations.length > 0 && <p className="text-[10px] text-gray-600 mt-1 italic">{f.limitations[0]}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right: Query + Insights */}
            <div className="lg:col-span-4 flex flex-col gap-4">
              {/* Query */}
              <div className="glass-panel-accent p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <span className="text-blue-400">◆</span> Change Analysis Query
                </h3>
                <div className="flex flex-col gap-2">
                  <input type="text" value={query} onChange={e => setQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                    placeholder="What has changed between these images?"
                    className="w-full bg-gray-900/60 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors" />
                  <button onClick={handleSubmit}
                    disabled={loading || !beforeFile || !afterFile}
                    className="btn-primary w-full disabled:opacity-50">
                    {loading ? 'Analyzing...' : result ? 'Ask Follow-up' : 'Analyze Changes'}
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {['What has changed?', 'How many new buildings?', 'Where is the biggest change?', 'Is there flooding?', 'Which department should investigate?'].map((s, i) => (
                    <button key={i} onClick={() => setQuery(s)}
                      className="text-[10px] px-2 py-1 rounded-full bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/20">{s}</button>
                  ))}
                </div>
              </div>

              {/* Chat */}
              <div className="glass-panel flex-1 flex flex-col overflow-hidden min-h-[200px]">
                <div className="p-3 border-b border-gray-800 text-xs font-semibold text-gray-400">CONVERSATION</div>
                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} fade-in`}>
                      <div className={`max-w-[90%] rounded-lg px-3 py-2 text-xs ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-200'}`}>
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-800 rounded-lg px-4 py-2 text-sm">
                        <span className="inline-flex gap-1">
                          <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"></span>
                          <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                          <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                        </span>
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>
              </div>

              {/* Government Insight */}
              {result?.government_use && (
                <div className="glass-panel p-4 fade-in">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">Government Insight</h3>
                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-gray-500">Department</span>
                      <p className="text-blue-400 font-medium">{result.government_use.department}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Issue</span>
                      <p className="text-gray-300">{result.government_use.issue}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">Priority</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold priority-${result.government_use.priority.toLowerCase()}`}>
                        {result.government_use.priority}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Recommended Action</span>
                      <p className="text-gray-300">{result.government_use.recommended_action}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Reasoning</span>
                      <p className="text-gray-400 italic">{result.government_use.reasoning}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Report + Actions */}
              {result && (
                <div className="flex gap-2 fade-in">
                  <button onClick={handleReport} className="btn-primary flex-1 text-sm">📄 Generate Report</button>
                </div>
              )}

              {/* Limitations */}
              {result && result.limitations.length > 0 && (
                <div className="glass-panel p-3 fade-in">
                  <h4 className="text-[10px] font-semibold text-gray-500 mb-1">LIMITATIONS</h4>
                  {result.limitations.map((l, i) => <p key={i} className="text-[10px] text-gray-600">{l}</p>)}
                </div>
              )}

              {/* Mode Badge */}
              {result && (
                <div className="text-center text-[10px] text-gray-600">
                  Analysis Mode: {result.mode === 'demo' ? '● DEMO MODE' : '● LIVE AI'}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
