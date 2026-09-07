import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface HealthStatus {
  status: string;
  app: string;
  version: string;
  database: string;
}

interface Observation {
  observation_id: string;
  source_id: string;
  route_id: string;
  carrier_id: string;
  travel_date: string;
  observed_at: string;
  booking_horizon_days: number;
  cabin: string;
  base_fare: number;
  taxes: number;
  mandatory_fees: number;
  total_fare: number;
  currency: string;
  data_status: string;
  normalization_result?: {
    normalized_total: number;
    normalization_version: string;
  };
  quality_result?: {
    eligible: boolean;
    outlier_status: string;
  };
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedRoute, setSelectedRoute] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  const API_BASE = 'http://localhost:8000/api/v1';

  const checkHealth = async () => {
    try {
      const res = await axios.get<HealthStatus>(`${API_BASE}/health`);
      setHealth(res.data);
      setHealthError(null);
    } catch (err: any) {
      setHealthError(err.message || 'Failed to connect to backend server');
    }
  };

  const fetchObservations = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/observations?limit=50`;
      if (selectedRoute) url += `&route_id=${selectedRoute}`;
      if (selectedStatus) url += `&data_status=${selectedStatus}`;
      
      const res = await axios.get<Observation[]>(url);
      setObservations(res.data);
    } catch (err: any) {
      console.error("Error fetching observations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    fetchObservations();
  }, [selectedRoute, selectedStatus]);

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ borderBottom: '1px solid #334155', paddingBottom: '16px', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', color: '#6366f1' }}>AeroCPI — Airfare Measurement Platform Shell</h1>
        <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '14px' }}>
          Experimental Prototype for CPI Augmentation | Milestone 1 Foundational Domain Layer
        </p>

        <div style={{ marginTop: '16px', display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ padding: '8px 16px', borderRadius: '6px', backgroundColor: '#1e293b', border: '1px solid #334155', fontSize: '14px' }}>
            Backend API: <strong>{healthError ? 'DISCONNECTED' : health ? 'CONNECTED' : 'CHECKING...'}</strong>
            {health && ` (${health.app} v${health.version})`}
          </div>

          <div style={{ padding: '8px 16px', borderRadius: '6px', backgroundColor: '#1e293b', border: '1px solid #334155', fontSize: '14px' }}>
            Database: <strong style={{ color: health?.database === 'connected' ? '#10b981' : '#ef4444' }}>
              {health?.database || 'UNKNOWN'}
            </strong>
          </div>

          <button 
            onClick={() => { checkHealth(); fetchObservations(); }}
            style={{ padding: '8px 16px', backgroundColor: '#4f46e5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
          >
            Refresh Status
          </button>
        </div>
      </header>

      {/* Filter Controls */}
      <section style={{ marginBottom: '20px', display: 'flex', gap: '16px', alignItems: 'center' }}>
        <label style={{ fontSize: '14px', color: '#cbd5e1' }}>
          Filter Route:
          <select 
            value={selectedRoute} 
            onChange={(e) => setSelectedRoute(e.target.value)}
            style={{ marginLeft: '8px', padding: '6px 12px', borderRadius: '4px', backgroundColor: '#1e293b', color: '#fff', border: '1px solid #475569' }}
          >
            <option value="">All Routes</option>
            <option value="DEL-BOM">DEL-BOM</option>
            <option value="BOM-DEL">BOM-DEL</option>
            <option value="BLR-DEL">BLR-DEL</option>
            <option value="CCU-DEL">CCU-DEL</option>
            <option value="DEL-MAA">DEL-MAA</option>
          </select>
        </label>

        <label style={{ fontSize: '14px', color: '#cbd5e1' }}>
          Filter Data Status:
          <select 
            value={selectedStatus} 
            onChange={(e) => setSelectedStatus(e.target.value)}
            style={{ marginLeft: '8px', padding: '6px 12px', borderRadius: '4px', backgroundColor: '#1e293b', color: '#fff', border: '1px solid #475569' }}
          >
            <option value="">All Statuses</option>
            <option value="OBSERVED">OBSERVED</option>
            <option value="FROZEN">FROZEN</option>
            <option value="SYNTHETIC">SYNTHETIC</option>
            <option value="DEMO">DEMO</option>
          </select>
        </label>

        <span style={{ fontSize: '14px', color: '#94a3b8', marginLeft: 'auto' }}>
          Showing {observations.length} observations
        </span>
      </section>

      {/* Observations Table */}
      <main>
        {loading ? (
          <p style={{ color: '#94a3b8' }}>Loading observations from AeroCPI API...</p>
        ) : observations.length === 0 ? (
          <div style={{ padding: '32px', backgroundColor: '#1e293b', borderRadius: '8px', textAlign: 'center' }}>
            <p style={{ color: '#94a3b8', margin: 0 }}>No observations found. Run `python scripts/seed_demo_data.py` to seed sample data.</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: '#1e293b', borderRadius: '8px', overflow: 'hidden' }}>
            <thead>
              <tr style={{ backgroundColor: '#0f172a', textAlign: 'left', borderBottom: '2px solid #334155' }}>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Route</th>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Carrier</th>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Travel Date</th>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Horizon</th>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Base Fare</th>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Taxes & Fees</th>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Total Fare</th>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Normalized</th>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Data Status</th>
                <th style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>Quality</th>
              </tr>
            </thead>
            <tbody>
              {observations.map((obs) => (
                <tr key={obs.observation_id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '12px', fontWeight: 600 }}>{obs.route_id}</td>
                  <td style={{ padding: '12px' }}>{obs.carrier_id}</td>
                  <td style={{ padding: '12px' }}>{obs.travel_date}</td>
                  <td style={{ padding: '12px' }}>T+{obs.booking_horizon_days}</td>
                  <td style={{ padding: '12px' }}>₹{obs.base_fare.toFixed(2)}</td>
                  <td style={{ padding: '12px' }}>₹{(obs.taxes + obs.mandatory_fees).toFixed(2)}</td>
                  <td style={{ padding: '12px', fontWeight: 600, color: '#10b981' }}>₹{obs.total_fare.toFixed(2)}</td>
                  <td style={{ padding: '12px' }}>
                    ₹{obs.normalization_result?.normalized_total.toFixed(2) || '—'}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{ 
                      padding: '4px 8px', 
                      borderRadius: '4px', 
                      fontSize: '11px', 
                      fontWeight: 600,
                      backgroundColor: obs.data_status === 'OBSERVED' ? '#065f46' : obs.data_status === 'SYNTHETIC' ? '#92400e' : '#3730a3',
                      color: '#fff'
                    }}>
                      {obs.data_status}
                    </span>
                  </td>
                  <td style={{ padding: '12px', fontSize: '12px', color: '#94a3b8' }}>
                    {obs.quality_result?.outlier_status || 'VALID'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>
    </div>
  );
}
