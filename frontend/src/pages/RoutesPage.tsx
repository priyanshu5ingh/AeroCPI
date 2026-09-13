import React, { useState, useEffect } from 'react';
import {
  Compass,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  Layers,
  ShieldCheck,
  Search,
  Calendar,
  Clock,
  RefreshCw,
  ExternalLink,
  Info,
  CheckCircle2,
  FileText
} from 'lucide-react';
import { IndexDashboardResponse, IndexExplanationResponse, RouteIntelligenceResponse } from '../types';
import { fetchRouteIntelligence } from '../services/api';

interface RoutesPageProps {
  dashboard: IndexDashboardResponse;
  explanation?: IndexExplanationResponse | null;
  onSelectRoute?: (routeId: string) => void;
  onNavigateToExplorer?: (routeId: string) => void;
}

// 10 Sovereign DGCA corridors ranked from largest positive contribution to largest negative contribution
const CORRIDOR_ROSTER = [
  { id: 'DEL-HYD', origin: 'DEL', destination: 'HYD', name: 'Delhi – Hyderabad', weightPct: 10.3, pointContrib: 1.0675 },
  { id: 'BLR-CCU', origin: 'BLR', destination: 'CCU', name: 'Bengaluru – Kolkata', weightPct: 6.1, pointContrib: 0.3269 },
  { id: 'BLR-HYD', origin: 'BLR', destination: 'HYD', name: 'Bengaluru – Hyderabad', weightPct: 7.3, pointContrib: 0.2805 },
  { id: 'DEL-PAT', origin: 'DEL', destination: 'PAT', name: 'Delhi – Patna', weightPct: 6.6, pointContrib: 0.2125 },
  { id: 'BLR-BOM', origin: 'BLR', destination: 'BOM', name: 'Bengaluru – Mumbai', weightPct: 11.6, pointContrib: 0.1499 },
  { id: 'DEL-CCU', origin: 'DEL', destination: 'CCU', name: 'Delhi – Kolkata', weightPct: 9.9, pointContrib: 0.0000 },
  { id: 'DEL-BOM', origin: 'DEL', destination: 'BOM', name: 'Delhi – Mumbai', weightPct: 17.8, pointContrib: -0.0026 },
  { id: 'MAA-DEL', origin: 'MAA', destination: 'DEL', name: 'Chennai – Delhi', weightPct: 8.2, pointContrib: -0.2993 },
  { id: 'BLR-DEL', origin: 'BLR', destination: 'DEL', name: 'Bengaluru – Delhi', weightPct: 14.1, pointContrib: -0.7875 },
  { id: 'GOI-BOM', origin: 'GOI', destination: 'BOM', name: 'Goa – Mumbai', weightPct: 8.0, pointContrib: -4.7391 },
];

export const RoutesPage: React.FC<RoutesPageProps> = ({
  dashboard,
  explanation,
  onSelectRoute,
  onNavigateToExplorer,
}) => {
  const scope = dashboard.dashboard_scope;
  const [selectedRouteId, setSelectedRouteId] = useState<string>('DEL-HYD');
  const [intelligence, setIntelligence] = useState<RouteIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load corridor intelligence from backend API
  const loadIntelligence = async (routeId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRouteIntelligence(routeId, scope.run_id);
      setIntelligence(data);
    } catch (err: any) {
      console.error(`Failed to load route intelligence for ${routeId}:`, err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch route intelligence');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIntelligence(selectedRouteId);
  }, [selectedRouteId, scope.run_id]);

  const activeRosterItem = CORRIDOR_ROSTER.find((c) => c.id === selectedRouteId) || CORRIDOR_ROSTER[0];

  const isUp = intelligence ? intelligence.direction === 'POSITIVE' : activeRosterItem.pointContrib > 0;
  const isDown = intelligence ? intelligence.direction === 'NEGATIVE' : activeRosterItem.pointContrib < 0;

  return (
    <div className="space-y-8">
      {/* 1. Header & Sovereign Basket Selector Bar */}
      <div className="surface-solid p-6 sm:p-8 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200/80">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                  ROUTE CORRIDOR INTELLIGENCE
                </h1>
                <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200/80 uppercase">
                  10 DGCA Corridors
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Inspect elementary corridor index trajectories, official DGCA passenger weights (w_r*), and 5-horizon term structures.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap text-xs font-mono">
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-1.5 text-slate-700 shadow-xs">
              <span className="text-slate-400 mr-1.5">RUN:</span>
              <span className="font-bold text-slate-900">{scope.run_id.substring(0, 8)}...</span>
            </div>

            <div className="bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-1.5 text-slate-700 shadow-xs">
              <span className="text-slate-400 mr-1.5">CABIN:</span>
              <span className="font-bold text-emerald-700">{scope.cabin}</span>
            </div>

            <div className="bg-emerald-50 text-emerald-700 border border-emerald-200/90 rounded-xl px-3 py-1.5 text-[11px] font-bold shadow-xs flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>SERVER-CERTIFIED</span>
            </div>
          </div>
        </div>

        {/* 10 Corridor Ranking Selector Strip */}
        <div>
          <div className="flex items-center justify-between pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            <span>Sovereign Basket Corridors (Ranked: Largest Positive to Largest Negative Contribution)</span>
            <span>Click to isolate corridor</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-2">
            {CORRIDOR_ROSTER.map((item) => {
              const isSelected = item.id === selectedRouteId;
              const isPos = item.pointContrib > 0;
              const isNeg = item.pointContrib < 0;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedRouteId(item.id)}
                  className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-1.5 ${
                    isSelected
                      ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/20 -translate-y-[1px]'
                      : 'bg-slate-50/80 hover:bg-slate-100 border-slate-200/80 text-slate-700 hover:-translate-y-[1px] hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs">{item.id}</span>
                    <span
                      className={`text-[9px] font-mono font-semibold px-1 rounded ${
                        isSelected ? 'bg-white/20 text-white' : 'bg-slate-200/70 text-slate-600'
                      }`}
                    >
                      {item.weightPct}%
                    </span>
                  </div>

                  <span
                    className={`font-mono text-[10px] font-bold ${
                      isSelected
                        ? 'text-blue-100'
                        : isPos
                        ? 'text-rose-600'
                        : isNeg
                        ? 'text-emerald-600'
                        : 'text-slate-500'
                    }`}
                  >
                    {item.pointContrib > 0 ? '+' : ''}
                    {item.pointContrib.toFixed(2)} pts
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 2. Selected Corridor Spotlight Hero Card */}
      <div className="surface-solid p-6 sm:p-8 relative overflow-hidden">
        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-400">
            <RefreshCw className="w-6 h-6 text-blue-500 animate-spin" />
            <span className="text-xs font-semibold">Loading corridor intelligence for {selectedRouteId}...</span>
          </div>
        ) : error ? (
          <div className="py-12 text-center text-rose-600 space-y-2">
            <p className="text-sm font-semibold">{error}</p>
            <button
              type="button"
              onClick={() => loadIntelligence(selectedRouteId)}
              className="px-3 py-1.5 rounded-lg bg-rose-50 border border-rose-200 text-xs font-bold hover:bg-rose-100 cursor-pointer"
            >
              Retry
            </button>
          </div>
        ) : intelligence ? (
          <div className="space-y-8">
            {/* Top Spotlight Bar */}
            <div className="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-6 pb-6 border-b border-slate-100">
              <div className="space-y-3 max-w-2xl">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-[11px] font-mono font-bold uppercase">
                    CORRIDOR SPOTLIGHT
                  </span>
                  <span className="font-mono text-xs font-bold text-slate-800">
                    {intelligence.route_id}
                  </span>
                  <span className="text-slate-300">·</span>
                  <span className="text-xs text-slate-500 font-medium">
                    {activeRosterItem.name}
                  </span>
                </div>

                {/* Index Level & Movement Pill */}
                <div className="flex items-baseline gap-4 flex-wrap pt-1">
                  <h2 className="text-5xl font-black text-slate-900 tracking-tight mono-number">
                    {intelligence.route_index_value.toFixed(2)}
                  </h2>

                  <div
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold border ${
                      isDown
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : isUp
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : 'bg-slate-50 text-slate-700 border-slate-200'
                    }`}
                  >
                    {isDown && <TrendingDown className="w-3.5 h-3.5 text-emerald-600" />}
                    {isUp && <TrendingUp className="w-3.5 h-3.5 text-rose-600" />}
                    {!isDown && !isUp && <Minus className="w-3.5 h-3.5 text-slate-500" />}
                    <span className="font-mono">
                      {intelligence.point_contribution !== null
                        ? `${intelligence.point_contribution > 0 ? '+' : ''}${intelligence.point_contribution.toFixed(4)} index shift`
                        : 'Neutral'}
                    </span>
                  </div>

                  {/* Cross-Module Navigation Action */}
                  <div className="flex items-center gap-2">
                    {onNavigateToExplorer && (
                      <button
                        type="button"
                        onClick={() => onNavigateToExplorer(selectedRouteId)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 text-blue-700 border border-blue-200/80 text-xs font-bold hover:bg-blue-100 transition-all cursor-pointer shadow-xs"
                      >
                        <Search className="w-3.5 h-3.5" />
                        <span>Explore Raw Evidence Quotes →</span>
                      </button>
                    )}

                    {onSelectRoute && (
                      <button
                        type="button"
                        onClick={() => onSelectRoute(selectedRouteId)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 text-slate-700 border border-slate-200 text-xs font-bold hover:bg-slate-100 transition-all cursor-pointer shadow-xs"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Inspect 5A Attribution →</span>
                      </button>
                    )}
                  </div>
                </div>

                <p className="text-sm text-slate-700 font-medium leading-relaxed">
                  Representative airfare shifted from{' '}
                  <span className="font-mono font-bold text-slate-900">
                    ₹{intelligence.base_representative_fare.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
                  </span>{' '}
                  to{' '}
                  <span className="font-mono font-bold text-slate-900">
                    ₹{intelligence.current_representative_fare.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
                  </span>{' '}
                  on the headline horizon, representing a price relative of{' '}
                  <span className="font-mono font-bold text-blue-600">
                    {(intelligence.route_index_value / 100).toFixed(4)}
                  </span>
                  .
                </p>
              </div>

              {/* Corridor Weights & Metrics Rail */}
              <div className="xl:border-l xl:border-slate-100 xl:pl-8 grid grid-cols-2 gap-3 min-w-[280px]">
                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/80">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                    DGCA Weight (wr)
                  </span>
                  <span className="text-base font-bold font-mono text-slate-900 mt-0.5 block">
                    {(intelligence.dgca_weight * 100).toFixed(2)}%
                  </span>
                  <span className="text-[10px] text-slate-400 font-sans">Sovereign Basket Share</span>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/80">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                    Active Weight
                  </span>
                  <span className="text-base font-bold font-mono text-blue-700 mt-0.5 block">
                    {(intelligence.active_weight * 100).toFixed(2)}%
                  </span>
                  <span className="text-[10px] text-slate-400 font-sans">Normalized Matched</span>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/80">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                    Corridor Coverage
                  </span>
                  <span className="text-base font-bold font-mono text-emerald-700 mt-0.5 block">
                    {(intelligence.coverage_ratio * 100).toFixed(0)}%
                  </span>
                  <span className="text-[10px] text-slate-400 font-sans">10 / 10 Complete</span>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/80">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                    Sample Quality
                  </span>
                  <span className="text-base font-bold font-mono text-slate-900 mt-0.5 block">
                    {intelligence.quality_summary.completeness}
                  </span>
                  <span className="text-[10px] text-slate-400 font-sans">
                    {intelligence.quality_summary.anomalies_detected} anomalies
                  </span>
                </div>
              </div>
            </div>

            {/* 3. 5-Horizon Term Structure for this Corridor */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <Clock className="w-4 h-4 text-blue-600" />
                    <span>5-Horizon Advance Booking Term Structure</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Evolution of representative fares and price relatives along {selectedRouteId} across booking horizons.
                  </p>
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  T+1 through T+45 Booking Windows
                </span>
              </div>

              {/* Table of 5 Horizons for this Corridor */}
              <div className="overflow-x-auto rounded-xl border border-slate-200/90">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50/90 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                      <th className="py-3 px-4">Horizon</th>
                      <th className="py-3 px-4">Lead Window</th>
                      <th className="py-3 px-4 text-right">Base Fare (Ref)</th>
                      <th className="py-3 px-4 text-right">Current Fare (Calc)</th>
                      <th className="py-3 px-4 text-right">Price Relative</th>
                      <th className="py-3 px-4 text-right">Point Contribution</th>
                      <th className="py-3 px-4 text-center">Horizon Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {intelligence.horizon_results.map((hr) => {
                      const isHeadline = hr.horizon_code === 'T+15';
                      const relPercent = (hr.price_relative * 100).toFixed(2);
                      const isHrUp = hr.point_contribution !== null && hr.point_contribution > 0;
                      const isHrDown = hr.point_contribution !== null && hr.point_contribution < 0;

                      let leadDesc = 'Advance Horizon';
                      if (hr.horizon_code === 'T+1') leadDesc = 'Distressed / 1-Day Lead';
                      else if (hr.horizon_code === 'T+7') leadDesc = '1-Week Parity Lead';
                      else if (hr.horizon_code === 'T+15') leadDesc = 'AeroCPI Headline Horizon';
                      else if (hr.horizon_code === 'T+30') leadDesc = '1-Month Advance Lead';
                      else if (hr.horizon_code === 'T+45') leadDesc = '6-Week Advance Booking';

                      return (
                        <tr
                          key={hr.horizon_code}
                          className={`${
                            isHeadline ? 'bg-blue-50/40 font-bold' : 'hover:bg-slate-50/60'
                          }`}
                        >
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                                isHeadline
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-slate-100 text-slate-700'
                              }`}
                            >
                              {hr.horizon_code}
                            </span>
                          </td>

                          <td className="py-3 px-4 font-sans text-slate-600">
                            {leadDesc}
                          </td>

                          <td className="py-3 px-4 text-right text-slate-700">
                            ₹{hr.base_representative_fare.toFixed(2)}
                          </td>

                          <td className="py-3 px-4 text-right text-slate-900 font-bold">
                            ₹{hr.current_representative_fare.toFixed(2)}
                          </td>

                          <td className="py-3 px-4 text-right">
                            <span className="text-slate-800">
                              {relPercent}
                            </span>
                          </td>

                          <td className="py-3 px-4 text-right">
                            <span
                              className={`font-bold ${
                                isHrUp ? 'text-rose-600' : isHrDown ? 'text-emerald-600' : 'text-slate-500'
                              }`}
                            >
                              {hr.point_contribution !== null
                                ? `${hr.point_contribution > 0 ? '+' : ''}${hr.point_contribution.toFixed(4)}`
                                : '0.0000'}
                            </span>
                          </td>

                          <td className="py-3 px-4 text-center">
                            {isHeadline ? (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 font-sans">
                                HEADLINE
                              </span>
                            ) : (
                              <span className="text-slate-400 text-[10px] font-sans">
                                Term Structure
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 4. Statutory & Methodological Disclaimer */}
            <div className="pt-4 border-t border-slate-100 flex items-start gap-2 text-xs text-slate-500">
              <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <span>
                AeroCPI corridor elementary price relatives are derived using Jevons geometric means across matched quotes. Corridor weights are determined from official DGCA scheduled domestic passenger volume figures and do not measure airline revenue yield. AeroCPI is not statistically equivalent to CPI.
              </span>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};
