'use client';
import Link from 'next/link';
import Navbar from '@/components/Navbar';

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main className="pt-14">
        {/* Hero */}
        <section className="relative min-h-[85vh] flex flex-col items-center justify-center px-6 overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(59,130,246,0.08)_0%,transparent_70%)]" />
          <div className="relative z-10 max-w-4xl mx-auto text-center fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-8">
              <span className="w-2 h-2 rounded-full bg-blue-400 pulse-dot"></span>
              SIH 2026 — Problem Statement SIH26167
            </div>
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
              <span className="gradient-text">Ask Your Satellite Image</span>
              <br />
              <span className="text-white">Anything.</span>
            </h1>
            <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
              SatQuery AI transforms complex satellite imagery into natural-language insights
              for faster geospatial decision-making.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/analyze" className="btn-primary text-base px-8 py-3">
                Analyze Image
              </Link>
              <Link href="/compare" className="btn-primary text-base px-8 py-3 !bg-gradient-to-r !from-purple-600 !to-blue-600">
                Compare Before &amp; After
              </Link>
              <Link href="/analyze?demo=urban" className="btn-secondary text-base px-8 py-3">
                Try Demo
              </Link>
            </div>
          </div>
        </section>

        {/* Value Proposition */}
        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-16 text-white">
              From Imagery to Intelligence in Seconds
            </h2>
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div className="glass-panel p-8">
                <h3 className="text-lg font-semibold text-red-400 mb-4">Traditional Workflow</h3>
                <div className="space-y-3">
                  {['Satellite Imagery', 'GIS Software', 'Expert Interpretation', 'Manual Analysis', 'Report'].map((step, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center text-xs text-red-400">{i + 1}</div>
                      <span className="text-gray-400">{step}</span>
                      {i < 4 && <span className="text-gray-600 ml-auto">→</span>}
                    </div>
                  ))}
                  <p className="text-sm text-gray-500 mt-4 pt-4 border-t border-gray-800">Hours to days per analysis</p>
                </div>
              </div>
              <div className="glass-panel-accent p-8">
                <h3 className="text-lg font-semibold text-blue-400 mb-4">SatQuery AI</h3>
                <div className="space-y-3">
                  {['Satellite Imagery', 'Ask a Question', 'AI Interpretation', 'Visual Evidence', 'Government Insight'].map((step, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-xs text-blue-400">{i + 1}</div>
                      <span className="text-gray-200">{step}</span>
                      {i < 4 && <span className="text-blue-600 ml-auto">→</span>}
                    </div>
                  ))}
                  <p className="text-sm text-blue-400/70 mt-4 pt-4 border-t border-blue-900/50">Seconds per analysis</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="py-20 px-6 border-t border-gray-800/50">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-4 text-white">Key Capabilities</h2>
            <p className="text-center text-gray-400 mb-12 max-w-xl mx-auto">AI-assisted satellite imagery analysis for screening and decision-support</p>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                { icon: '🔍', title: 'Object Detection', desc: 'Identify buildings, roads, water bodies, vegetation in satellite imagery' },
                { icon: '🔄', title: 'Change Detection', desc: 'Compare before & after imagery to detect urban expansion, flooding, deforestation' },
                { icon: '📊', title: 'Land Cover Analysis', desc: 'AI-estimated visual composition — built-up, vegetation, water, bare land' },
                { icon: '🏛️', title: 'Government Insights', desc: 'Route findings to relevant departments with priority and recommended actions' },
                { icon: '🌊', title: 'Flood Screening', desc: 'Visual flood impact assessment with severity indicators and affected areas' },
                { icon: '📄', title: 'Report Generation', desc: 'Professional PDF reports with evidence, confidence, and disclaimers' },
              ].map((feat, i) => (
                <div key={i} className="glass-panel p-6 hover:border-blue-500/30 transition-colors">
                  <span className="text-3xl mb-4 block">{feat.icon}</span>
                  <h3 className="font-semibold text-white mb-2">{feat.title}</h3>
                  <p className="text-sm text-gray-400">{feat.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Disclaimer */}
        <section className="py-12 px-6 border-t border-gray-800/50">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-xs text-gray-500 leading-relaxed">
              SatQuery AI provides AI-assisted visual interpretation for screening and decision-support.
              Not a substitute for official survey, legal determination, cadastral records, or field verification.
              Uploaded imagery is processed by the configured AI provider when Live AI mode is enabled.
            </p>
          </div>
        </section>
      </main>
    </>
  );
}
