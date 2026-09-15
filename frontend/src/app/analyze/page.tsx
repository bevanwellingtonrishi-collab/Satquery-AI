'use client';
import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Navbar from '@/components/Navbar';
import { analyzeImage, followUp, getDemoScenes, getDemoImageUrl, generateReport } from '@/lib/api';
import type { AnalysisResponse, DemoScene, ChatMessage, Finding, ObjectDetection } from '@/types';

const SUGGESTIONS = [
  'What objects are present in this image?',
  'How many buildings are visible?',
  'Describe this area',
  'Analyze vegetation cover',
  'Find water bodies',
  'Is this area urban or rural?',
  'Which area has the highest building density?',
  'Identify roads and infrastructure',
];

function AnalyzePageInner() {
  const searchParams = useSearchParams();
  const [image, setImage] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string>('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState('');
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse | null>(null);
  const [showRegions, setShowRegions] = useState(true);
  const [demoScenes, setDemoScenes] = useState<DemoScene[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getDemoScenes().then(d => setDemoScenes(d.scenes)).catch(() => {});
  }, []);

  useEffect(() => {
    const demo = searchParams.get('demo');
    if (demo) loadDemoScene(demo);
  }, [searchParams]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadDemoScene = async (sceneId: string) => {
    const url = getDemoImageUrl(sceneId);
    setImageUrl(url);
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      const file = new File([blob], `${sceneId}.png`, { type: 'image/png' });
      setImage(file);
    } catch (e) {
      console.error('Failed to load demo scene', e);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(file);
      setImageUrl(URL.createObjectURL(file));
      setMessages([]);
      setSessionId('');
      setCurrentAnalysis(null);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      setImage(file);
      setImageUrl(URL.createObjectURL(file));
      setMessages([]);
      setSessionId('');
      setCurrentAnalysis(null);
    }
  }, []);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    if (!image && !sessionId) return;

    const userMsg: ChatMessage = { role: 'user', content: query, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    const q = query;
    setQuery('');

    try {
      let result: AnalysisResponse;
      if (sessionId && messages.length > 0) {
        result = await followUp(q, sessionId);
      } else if (image) {
        result = await analyzeImage(image, q, sessionId);
      } else {
        throw new Error('No image or session');
      }

      if (!sessionId) setSessionId(result.session_id);
      setCurrentAnalysis(result);

      const aiMsg: ChatMessage = {
        role: 'assistant',
        content: result.answer,
        timestamp: Date.now(),
        analysis: result,
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (e: any) {
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: `Error: ${e.message || 'Analysis failed. Please try again.'}`,
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleReport = async () => {
    if (!currentAnalysis) return;
    try {
      const blob = await generateReport(
        messages.find(m => m.role === 'user')?.content || 'Analysis',
        currentAnalysis,
        image?.name || 'satellite_image',
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'satquery_report.pdf';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Report generation failed', e);
    }
  };

  // Collect all regions from current analysis for overlay
  const allRegions: { region: { x: number; y: number; width: number; height: number }; label: string }[] = [];
  if (currentAnalysis && showRegions) {
    currentAnalysis.findings?.forEach((f: Finding) => {
      if (f.region) allRegions.push({ region: f.region, label: f.finding.substring(0, 40) });
    });
    currentAnalysis.objects?.forEach((o: ObjectDetection) => {
      o.regions?.forEach(r => allRegions.push({ region: r, label: `${o.label} (${o.count})` }));
    });
  }

  return (
    <>
      <Navbar />
      <main className="pt-16 min-h-screen">
        <div className="max-w-[1800px] mx-auto px-4 py-4 grid grid-cols-1 lg:grid-cols-12 gap-4" style={{ height: 'calc(100vh - 64px)' }}>

          {/* Left: Upload + Scene Info */}
          <div className="lg:col-span-3 flex flex-col gap-4 overflow-y-auto">
            {/* Upload */}
            <div className="glass-panel p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Upload Image</h3>
              <div
                className="border-2 border-dashed border-gray-700 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500/50 transition-colors"
                onClick={() => fileInputRef.current?.click()}
                onDrop={handleDrop}
                onDragOver={e => e.preventDefault()}
              >
                <input ref={fileInputRef} type="file" accept="image/*,.tif,.tiff" className="hidden" onChange={handleFileChange} />
                <div className="text-3xl mb-2">🛰️</div>
                <p className="text-sm text-gray-400">Drop satellite imagery here</p>
                <p className="text-xs text-gray-600 mt-1">PNG, JPG, WebP, GeoTIFF</p>
              </div>
            </div>

            {/* Demo Scenes */}
            <div className="glass-panel p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Demo Scenes</h3>
              <div className="grid grid-cols-2 gap-2">
                {demoScenes.filter(s => !s.id.includes('2023') && !s.id.includes('2026')).map(scene => (
                  <button key={scene.id}
                    onClick={() => loadDemoScene(scene.id)}
                    className="text-left p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-xs">
                    <span className="block font-medium text-gray-300">{scene.name}</span>
                    <span className="text-gray-500 text-[10px]">{scene.category}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Scene Info */}
            {image && (
              <div className="glass-panel p-4 fade-in">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Scene Information</h3>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between"><span className="text-gray-500">File</span><span className="text-gray-300">{image.name}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Size</span><span className="text-gray-300">{(image.size / 1024).toFixed(0)} KB</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Type</span><span className="text-gray-300">{image.type || 'unknown'}</span></div>
                </div>
              </div>
            )}

            {/* Government Insight */}
            {currentAnalysis?.government_use && (
              <div className="glass-panel p-4 fade-in">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Government Insight</h3>
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-gray-500">Department</span>
                    <p className="text-blue-400 font-medium">{currentAnalysis.government_use.department}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Issue</span>
                    <p className="text-gray-300">{currentAnalysis.government_use.issue}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">Priority</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold priority-${currentAnalysis.government_use.priority.toLowerCase()}`}>
                      {currentAnalysis.government_use.priority}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Recommended Action</span>
                    <p className="text-gray-300">{currentAnalysis.government_use.recommended_action}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Reasoning</span>
                    <p className="text-gray-400 italic">{currentAnalysis.government_use.reasoning}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Center: Image Viewer */}
          <div className="lg:col-span-5 flex flex-col gap-4">
            <div className="glass-panel flex-1 relative overflow-hidden flex items-center justify-center min-h-[400px]">
              {imageUrl ? (
                <div className="relative w-full h-full flex items-center justify-center p-2">
                  <div className="relative inline-block max-w-full max-h-full">
                    <img src={imageUrl} alt="Satellite imagery" className="max-w-full max-h-[60vh] object-contain rounded" />
                    {/* Evidence regions overlay */}
                    {allRegions.map((r, i) => (
                      <div key={i} className="evidence-region" style={{
                        left: `${r.region.x * 100}%`,
                        top: `${r.region.y * 100}%`,
                        width: `${r.region.width * 100}%`,
                        height: `${r.region.height * 100}%`,
                      }}>
                        <span className="absolute -top-5 left-0 text-[9px] bg-blue-600/90 text-white px-1.5 py-0.5 rounded whitespace-nowrap">
                          {r.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center p-8">
                  <div className="text-5xl mb-4">🛰️</div>
                  <p className="text-gray-500">Upload or select a satellite image to begin</p>
                </div>
              )}
              {/* Toolbar */}
              {imageUrl && (
                <div className="absolute top-3 right-3 flex gap-1">
                  <button onClick={() => setShowRegions(!showRegions)}
                    className={`p-2 rounded text-xs ${showRegions ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400'}`}
                    title="Toggle detection regions">
                    📍
                  </button>
                </div>
              )}
              {/* Mode badge */}
              {currentAnalysis && (
                <div className="absolute bottom-3 left-3 text-[10px] px-2 py-1 rounded bg-black/60 text-gray-400">
                  {currentAnalysis.mode === 'demo' ? '● DEMO MODE' : '● LIVE AI'} | Confidence: {(currentAnalysis.confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>

            {/* Results: Objects + Land Cover */}
            {currentAnalysis && (
              <div className="grid grid-cols-2 gap-4 fade-in">
                {/* Detected Objects */}
                {currentAnalysis.objects.length > 0 && (
                  <div className="glass-panel p-4">
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">DETECTED FEATURES</h4>
                    <div className="space-y-1.5">
                      {currentAnalysis.objects.map((obj, i) => (
                        <div key={i} className="flex justify-between items-center text-xs">
                          <span className="text-gray-300">{obj.label}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-white font-semibold">{obj.count}</span>
                            <span className="text-gray-500">{(obj.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {/* Land Cover */}
                {currentAnalysis.land_cover && (
                  <div className="glass-panel p-4">
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">AI-ESTIMATED LAND COVER</h4>
                    <div className="space-y-2">
                      {[
                        { label: 'Built-up', value: currentAnalysis.land_cover.built_up, color: '#f59e0b' },
                        { label: 'Vegetation', value: currentAnalysis.land_cover.vegetation, color: '#22c55e' },
                        { label: 'Water', value: currentAnalysis.land_cover.water, color: '#3b82f6' },
                        { label: 'Bare Land', value: currentAnalysis.land_cover.bare_land, color: '#a16207' },
                      ].map((lc, i) => (
                        <div key={i}>
                          <div className="flex justify-between text-xs mb-0.5">
                            <span className="text-gray-400">{lc.label}</span>
                            <span className="text-gray-300">{lc.value}%</span>
                          </div>
                          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${lc.value}%`, background: lc.color }} />
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-[9px] text-gray-600 mt-2">AI-estimated visual proportions</p>
                  </div>
                )}
              </div>
            )}

            {/* Evidence Panel */}
            {currentAnalysis && currentAnalysis.findings.length > 0 && (
              <div className="glass-panel p-4 fade-in">
                <h4 className="text-xs font-semibold text-gray-400 mb-3">EVIDENCE-BASED FINDINGS</h4>
                <div className="space-y-3">
                  {currentAnalysis.findings.map((f, i) => (
                    <div key={i} className="border border-gray-800 rounded-lg p-3">
                      <div className="flex items-start justify-between mb-1">
                        <span className="text-sm text-gray-200 font-medium">{f.finding}</span>
                        <span className="text-xs px-2 py-0.5 rounded bg-blue-600/20 text-blue-400 ml-2 shrink-0">
                          {(f.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mb-1">{f.evidence_description}</p>
                      <div className="flex items-center gap-3 text-[10px]">
                        <span className="text-gray-500">Quality: <span className="text-gray-400 capitalize">{f.evidence_quality}</span></span>
                        {f.region && <span className="text-blue-500">📍 AI-estimated region</span>}
                      </div>
                      {f.limitations.length > 0 && (
                        <p className="text-[10px] text-gray-600 mt-1 italic">{f.limitations[0]}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: Query Panel + Chat */}
          <div className="lg:col-span-4 flex flex-col gap-4 overflow-hidden">
            <div className="glass-panel-accent flex-1 flex flex-col overflow-hidden">
              <div className="p-4 border-b border-gray-800">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <span className="text-blue-400">◆</span> AI Query Assistant
                </h3>
              </div>

              {/* Chat History */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 && (
                  <div className="text-center py-12">
                    <div className="text-4xl mb-3">💬</div>
                    <p className="text-sm text-gray-500 mb-4">Ask about the satellite image</p>
                    <div className="flex flex-wrap gap-2 justify-center">
                      {SUGGESTIONS.slice(0, 6).map((s, i) => (
                        <button key={i} onClick={() => setQuery(s)}
                          className="text-[11px] px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors border border-blue-500/20">
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} fade-in`}>
                    <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-200'
                    }`}>
                      {msg.content}
                      {msg.analysis && 'mode' in msg.analysis && (
                        <div className="mt-1 text-[10px] opacity-60">
                          {msg.analysis.mode === 'demo' ? '● Demo' : '● Live'} | {((msg.analysis as AnalysisResponse).confidence * 100).toFixed(0)}% confidence
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start fade-in">
                    <div className="bg-gray-800 rounded-lg px-4 py-3 text-sm text-gray-400">
                      <span className="inline-flex gap-1">
                        <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                      </span>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <div className="p-4 border-t border-gray-800">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
                    placeholder={image ? 'Ask about this satellite image...' : 'Upload an image first...'}
                    disabled={!image && !sessionId}
                    className="flex-1 bg-gray-900/60 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50 transition-colors"
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={loading || (!image && !sessionId) || !query.trim()}
                    className="btn-primary px-4 py-2.5 disabled:opacity-50"
                  >
                    {loading ? '...' : '→'}
                  </button>
                </div>
                {/* Actions */}
                {currentAnalysis && (
                  <div className="flex gap-2 mt-2">
                    <button onClick={handleReport} className="btn-secondary text-xs px-3 py-1.5">📄 Report</button>
                    <button onClick={() => setShowRegions(!showRegions)} className="btn-secondary text-xs px-3 py-1.5">
                      📍 {showRegions ? 'Hide' : 'Show'} Regions
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Limitations */}
            {currentAnalysis && currentAnalysis.limitations.length > 0 && (
              <div className="glass-panel p-3 fade-in">
                <h4 className="text-[10px] font-semibold text-gray-500 mb-1">LIMITATIONS</h4>
                {currentAnalysis.limitations.map((l, i) => (
                  <p key={i} className="text-[10px] text-gray-600">{l}</p>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading...</div>}>
      <AnalyzePageInner />
    </Suspense>
  );
}
