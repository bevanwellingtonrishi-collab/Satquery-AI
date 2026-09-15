/* SatQuery AI — API Client */
import type {
  AnalysisResponse,
  CompareResponse,
  StatusResponse,
  HistoryEntry,
  DemoScene,
} from '@/types';

// Empty string = relative URL (works on both localhost via Next.js rewrites and Vercel)
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

async function apiFetch(path: string, init?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res;
}

export async function getStatus(): Promise<StatusResponse> {
  const res = await apiFetch('/api/status');
  return res.json();
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await apiFetch('/api/health');
  return res.json();
}

export async function analyzeImage(
  image: File,
  query: string,
  sessionId: string = '',
): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append('image', image);
  form.append('query', query);
  if (sessionId) form.append('session_id', sessionId);

  const res = await apiFetch('/api/analyze', { method: 'POST', body: form });
  return res.json();
}

export async function followUp(
  query: string,
  sessionId: string,
): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append('query', query);
  form.append('session_id', sessionId);

  const res = await apiFetch('/api/followup', { method: 'POST', body: form });
  return res.json();
}

export async function compareImages(
  beforeImage: File,
  afterImage: File,
  query: string = 'What has changed between these two images?',
  sessionId: string = '',
): Promise<CompareResponse> {
  const form = new FormData();
  form.append('before_image', beforeImage);
  form.append('after_image', afterImage);
  form.append('query', query);
  if (sessionId) form.append('session_id', sessionId);

  const res = await apiFetch('/api/compare', { method: 'POST', body: form });
  return res.json();
}

export async function getHistory(limit: number = 50): Promise<{ entries: HistoryEntry[] }> {
  const res = await apiFetch(`/api/history?limit=${limit}`);
  return res.json();
}

export async function getDemoScenes(): Promise<{ scenes: DemoScene[] }> {
  const res = await apiFetch('/api/demo');
  return res.json();
}

export async function generateReport(
  query: string,
  analysis: object,
  imageName: string = '',
  heatmapBase64: string = '',
): Promise<Blob> {
  const form = new FormData();
  form.append('query', query);
  form.append('analysis_json', JSON.stringify(analysis));
  form.append('image_name', imageName);
  form.append('heatmap_base64', heatmapBase64);

  const res = await apiFetch('/api/report', { method: 'POST', body: form });
  return res.blob();
}

export function getDemoImageUrl(sceneId: string): string {
  return `${API_BASE}/api/demo/image/${sceneId}`;
}
