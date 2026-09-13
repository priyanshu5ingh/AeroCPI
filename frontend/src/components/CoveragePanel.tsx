import React from 'react';
import { Layers, CheckCircle2, TrendingUp } from 'lucide-react';
import { CoverageSummary } from '../types';

interface CoveragePanelProps {
  coverage: CoverageSummary;
}

export const CoveragePanel: React.FC<CoveragePanelProps> = ({ coverage }) => {
  const { horizon_coverage, headline_horizon_code } = coverage;

  return (
    <section className="bg-white rounded-2xl border border-slate-200/80 shadow-[0_2px_12px_-1px_rgba(15,23,42,0.03)] p-6 sm:p-8 space-y-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Forward Booking Horizon Curve
            </h2>
            <span className="text-xs text-slate-500 font-medium">
              Coverage: 100% DGCA Basket (10/10 Routes)
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Standard forward curve tracking passenger advance booking airfare structures from T+1 through T+45.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="font-medium text-slate-700">Coverage of AeroCPI basket</span>
          <span className="text-slate-300">|</span>
          <span className="flex items-center gap-1 text-emerald-600 font-semibold font-mono">
            <CheckCircle2 className="w-3.5 h-3.5" /> 10/10 active routes
          </span>
        </div>
      </div>

      {/* High-Fidelity SVG Curve Visualization */}
      <div className="relative w-full h-56 overflow-hidden rounded-xl bg-[#FAFBFD] border border-slate-100 p-4">
        <svg className="w-full h-full" viewBox="0 0 1000 200" fill="none" preserveAspectRatio="none">
          <defs>
            <linearGradient id="horizonCurveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#1D6AE5" stopOpacity="0.12" />
              <stop offset="100%" stopColor="#1D6AE5" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Reference Gridlines */}
          <line x1="0" y1="40" x2="1000" y2="40" stroke="#E2E8F0" strokeWidth="1" strokeDasharray="3 3" />
          <line x1="0" y1="90" x2="1000" y2="90" stroke="#E2E8F0" strokeWidth="1" strokeDasharray="3 3" />
          <line x1="0" y1="140" x2="1000" y2="140" stroke="#E2E8F0" strokeWidth="1" strokeDasharray="3 3" />

          {/* Axis Labels */}
          <text x="15" y="44" className="text-[10px] font-mono fill-slate-400">100.0 (Parity)</text>
          <text x="15" y="94" className="text-[10px] font-mono fill-slate-400">90.0</text>
          <text x="15" y="144" className="text-[10px] font-mono fill-slate-400">80.0</text>

          {/* Gradient Area Under Curve */}
          <path
            d="M 80 160 C 180 140, 220 42, 280 42 C 380 42, 420 60, 500 60 C 620 60, 660 88, 730 88 C 820 88, 860 96, 920 96 L 920 190 L 80 190 Z"
            fill="url(#horizonCurveGradient)"
          />

          {/* Main Spline Curve Line */}
          <path
            d="M 80 160 C 180 140, 220 42, 280 42 C 380 42, 420 60, 500 60 C 620 60, 660 88, 730 88 C 820 88, 860 96, 920 96"
            stroke="#1D6AE5"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* Milestone Nodes */}
          {/* T+1 (80, 160) */}
          <circle cx="80" cy="160" r="4.5" fill="#1D6AE5" stroke="#FFFFFF" strokeWidth="2" />
          {/* T+7 (280, 42) */}
          <circle cx="280" cy="42" r="4.5" fill="#1D6AE5" stroke="#FFFFFF" strokeWidth="2" />
          {/* T+15 (500, 60) - Headline Highlight */}
          <circle cx="500" cy="60" r="9" fill="#1D6AE5" fillOpacity="0.18" />
          <circle cx="500" cy="60" r="5.5" fill="#1D6AE5" stroke="#FFFFFF" strokeWidth="2.5" />
          <line x1="500" y1="10" x2="500" y2="190" stroke="#1D6AE5" strokeWidth="1.5" strokeDasharray="3 3" />
          {/* T+30 (730, 88) */}
          <circle cx="730" cy="88" r="4.5" fill="#1D6AE5" stroke="#FFFFFF" strokeWidth="2" />
          {/* T+45 (920, 96) */}
          <circle cx="920" cy="96" r="4.5" fill="#1D6AE5" stroke="#FFFFFF" strokeWidth="2" />
        </svg>
      </div>

      {/* Typographic Milestone Callout Grid Below Chart */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {horizon_coverage.map((h) => {
          const isHeadline = h.horizon_code === headline_horizon_code;
          const coveragePercent = Math.round(h.matched_coverage_ratio * 100);

          let subtitle = 'Advance Horizon';
          if (h.horizon_code === 'T+1') subtitle = 'Distressed / Tomorrow';
          else if (h.horizon_code === 'T+7') subtitle = '1-Week Parity Target';
          else if (h.horizon_code === 'T+15') subtitle = 'AeroCPI Headline';
          else if (h.horizon_code === 'T+30') subtitle = '1-Month Advance';
          else if (h.horizon_code === 'T+45') subtitle = '6-Week Booking';

          return (
            <div
              key={h.horizon_code}
              className={`p-4 rounded-xl border flex flex-col justify-between space-y-2 transition-all ${
                isHeadline
                  ? 'bg-blue-50/50 border-2 border-blue-500 shadow-sm relative'
                  : 'bg-slate-50/50 border-slate-200/70 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`text-xs font-mono font-bold ${isHeadline ? 'text-blue-700' : 'text-slate-600'}`}>
                  {h.horizon_code}
                </span>
                {isHeadline ? (
                  <span className="px-2 py-0.5 rounded bg-blue-600 text-white text-[10px] font-bold tracking-wide font-mono">
                    HEADLINE
                  </span>
                ) : (
                  <span className="text-slate-400 text-[10px] font-mono">
                    {coveragePercent}% matched
                  </span>
                )}
              </div>

              <div>
                <div className={`text-2xl font-bold font-mono tracking-tight ${isHeadline ? 'text-blue-900' : 'text-slate-900'}`}>
                  {h.index_value !== null ? h.index_value.toFixed(2) : '—'}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5 font-normal">
                  {subtitle}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-200/50 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>Matched: {coveragePercent}%</span>
                <span>{h.active_routes_count}/10 active</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
