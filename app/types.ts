/**
 * TypeScript types matching the backend API response.
 */

export interface PolicyAttribute {
  id: string;
  label: string;
  value: string;
  severity: "good" | "neutral" | "bad";
  evidence: string;
  weight: number;
  points_earned: number;
}

export interface AnalyzeResponse {
  service_name: string;
  domain: string;
  terms_url: string;
  privacy_url: string;
  trust_score: number;
  grade: string;
  analyzed_at: string;
  attributes: PolicyAttribute[];
  error?: string;
}
