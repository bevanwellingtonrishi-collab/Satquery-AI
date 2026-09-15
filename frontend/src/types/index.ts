/* SatQuery AI — Core TypeScript Types */

export interface EvidenceRegion {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Finding {
  finding: string;
  confidence: number;
  evidence_quality: string;
  evidence_description: string;
  limitations: string[];
  region: EvidenceRegion | null;
}

export interface ObjectDetection {
  label: string;
  count: number;
  confidence: number;
  regions: EvidenceRegion[];
}

export interface LandCover {
  built_up: number;
  vegetation: number;
  water: number;
  bare_land: number;
}

export interface GovernmentUse {
  department: string;
  issue: string;
  priority: string;
  recommended_action: string;
  reasoning: string;
}

export interface AnalysisResponse {
  answer: string;
  intent: string;
  confidence: number;
  objects: ObjectDetection[];
  land_cover: LandCover | null;
  findings: Finding[];
  observations: string[];
  evidence: string[];
  government_use: GovernmentUse | null;
  limitations: string[];
  session_id: string;
  mode: string;
}

export interface ChangeDetection {
  type: string;
  severity: string;
  description: string;
  confidence: number;
  evidence_description: string;
  region: EvidenceRegion | null;
}

export interface CompareResponse {
  overall_change: number;
  changes: ChangeDetection[];
  findings: Finding[];
  government_use: GovernmentUse | null;
  heatmap_base64: string;
  limitations: string[];
  session_id: string;
  mode: string;
}

export interface StatusResponse {
  mode: string;
  live_ai_available: boolean;
  provider: string | null;
  demo_available: boolean;
}

export interface HistoryEntry {
  id: number;
  timestamp: string;
  image_name: string;
  query: string;
  answer: string;
  intent: string;
  confidence: number;
  mode: string;
}

export interface DemoScene {
  id: string;
  name: string;
  description: string;
  image_url: string;
  category: string;
}

export interface GeoMetadata {
  crs: string | null;
  bounds: number[] | null;
  resolution: number[] | null;
  width: number | null;
  height: number | null;
  band_count: number | null;
  transform: number[] | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  analysis?: AnalysisResponse | CompareResponse;
}
