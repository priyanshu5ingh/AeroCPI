import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface HealthStatus {
  status: string;
  app: string;
  version: string;
  database: string;
}

interface IndexRun {
  run_id: string;
  run_timestamp: string;
  reference_period: string;
  comparison_period: string;
  dataset_version_id: string;
  number_of_observations: number;
  number_of_eligible_observations: number;
  number_of_excluded_observations: number;
  number_of_outlier_flagged: number;
  number_of_retained_warning: number;
  number_of_duplicates: number;
  coverage_ratio: number;
  index_value: number;
  canonical_run_fingerprint: str;
}

interface QualitySummary {
  total_observations: number;
  eligible_observations: number;
  excluded_observations: number;
  outlier_flagged_observations: number;
  retained_with_warning_observations: number;
  duplicate_observations: number;
  missing_incomplete_observations: number;
  coverage_ratio: number;
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [runs, setRuns] = useState<IndexRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<IndexRun | null>(null);
  const [qualitySummary, setQualitySummary] = useState<QualitySummary | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [executing, setExecuting] = useState<boolean>(false);

  const API_BASE = 'http://localhost:8000/api/v1';

  const checkHealth = async () => {
    try {
      const res = await axios.get<HealthStatus>(`${API_BASE}/health`);
      setHealth(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchIndexRuns = async () => {
    setLoading(true);
    try {
      const res = await axios.get<IndexRun[]>(`${API_BASE}/index-runs`);
      setRuns(res.data);
      if (res.data.length > 0) {
        selectRun(res.data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const selectRun = async (run: IndexRun) => {
    setSelectedRun(run);
    try {
      const res = await axios.get<QualitySummary>(`${API_BASE}/index-runs/${run.run_id}/quality-summary`);
      setQualitySummary(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const executeNewRun = async () => {
    setExecuting(true);
    try {
      const res = await axios.post<IndexRun>(`${API_BASE}/index-runs`, {
        reference_period: "2026-08-01",
        comparison_period: "2026-09-01",
        proxy_weight_version: "DGCA_PROXY_2026_V1"
      });
      await fetchIndexRuns();
    } catch (err: any) {
      alert("Failed to execute index run: " + (err.response?.data?.detail || err.message));
    } finally {
      setExecuting(false);
    }
  };

  useEffect(() => {
    checkHealth();
    fetchIndexRuns();
  }, []);

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif', backgroundColor: '#0f172a', color: '#f8fafc' }}>
      <header style={{ borderBottom: '1px solid #334155', paddingBottom: '16px', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, color: '#6366f1' }}>AeroCPI — Milestone 2 Index & Quality Engine Shell</h1>
        <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '14px' }}>
          Experimental prototype airfare price measurement intended to augment CPI airfare measurement.
        </p>

        <div style={{ marginTop: '16px', display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ padding: '8px 16px', borderRadius: '6px', backgroundColor: '#1e293b', border: '1px solid #334155' }}>
            Backend API: <strong>{health?.status === 'ok' ? 'CONNECTED' : 'DISCONNECTED'}</strong>
          </div>

          <button 
            onClick={executeNewRun}
            disabled={executing}
            style={{ padding: '8px 16px', backgroundColor: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
          >
            {executing ? 'Executing Pipeline...' : 'Run Index Engine (2026-08 vs 2026-09)'}
          </button>
        </div>
      </header>

      <main style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Left Column: Index Runs List */}
        <section>
          <h2>Index Runs ({runs.length})</h2>
          {loading ? (
            <p>Loading index runs...</p>
          ) : runs.length === 0 ? (
            <p style={{ color: '#94a3b8' }}>No index runs recorded yet. Click "Run Index Engine" above.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {runs.map((r) => (
                <div 
                  key={r.run_id}
                  onClick={() => selectRun(r)}
                  style={{ 
                    padding: '16px', 
                    borderRadius: '8px', 
                    backgroundColor: selectedRun?.run_id === r.run_id ? '#312e81' : '#1e293b', 
                    border: '1px solid #4338ca',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#10b981' }}>
                      AeroCPI Index: {r.index_value.toFixed(3)}
                    </span>
                    <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                      {new Date(r.run_timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div style={{ fontSize: '13px', color: '#cbd5e1' }}>
                    Reference Period: <strong>{r.reference_period}</strong> → Current: <strong>{r.comparison_period}</strong>
                  </div>

                  <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px', fontFamily: 'monospace' }}>
                    SHA-256 Fingerprint: {r.canonical_run_fingerprint.substring(0, 16)}...
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Right Column: Selected Run Details & Quality Summary */}
        <section>
          <h2>Index Run & Quality Summary</h2>
          {selectedRun ? (
            <div style={{ backgroundColor: '#1e293b', padding: '20px', borderRadius: '8px', border: '1px solid #334155' }}>
              <h3 style={{ margin: '0 0 12px 0', color: '#6366f1' }}>Run Metadata</h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '14px', lineHeight: '1.8' }}>
                <li><strong>Run ID:</strong> {selectedRun.run_id}</li>
                <li><strong>Reference Period:</strong> {selectedRun.reference_period}</li>
                <li><strong>Current Period:</strong> {selectedRun.comparison_period}</li>
                <li><strong>Dataset Version:</strong> {selectedRun.dataset_version_id}</li>
                <li><strong>Methodology:</strong> {selectedRun.methodology_version}</li>
                <li><strong>Weight Version:</strong> {selectedRun.proxy_weight_version}</li>
                <li><strong>Index Method:</strong> Jevons (Elementary) + Young/Laspeyres (National)</li>
              </ul>

              {qualitySummary && (
                <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #334155' }}>
                  <h3 style={{ margin: '0 0 12px 0', color: '#f59e0b' }}>Quality Metrics Summary</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '14px' }}>
                    <div>Total Observations: <strong>{qualitySummary.total_observations}</strong></div>
                    <div>Eligible Observations: <strong style={{ color: '#10b981' }}>{qualitySummary.eligible_observations}</strong></div>
                    <div>Excluded Observations: <strong style={{ color: '#ef4444' }}>{qualitySummary.excluded_observations}</strong></div>
                    <div>Outlier Flagged (MAD &gt; 3.5): <strong style={{ color: '#f59e0b' }}>{qualitySummary.outlier_flagged_observations}</strong></div>
                    <div>Duplicate Count: <strong>{qualitySummary.duplicate_observations}</strong></div>
                    <div>Coverage Ratio: <strong>{(qualitySummary.coverage_ratio * 100).toFixed(1)}%</strong></div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: '#94a3b8' }}>Select an Index Run from the left to view details.</p>
          )}
        </section>
      </main>
    </div>
  );
}
