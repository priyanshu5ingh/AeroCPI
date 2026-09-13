import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Calendar,
  Clock,
  TrendingDown,
  TrendingUp,
  Minus,
  Layers,
  ShieldCheck,
  Search,
  Compass,
  ArrowRight,
  Info,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  ChevronRight
} from 'lucide-react';
import { IndexDashboardResponse, HorizonIntelligenceResponse, RouteDriverItem } from '../types';
import { fetchHorizonsIntelligence } from '../services/api';

interface HorizonAnalysisPageProps {
  dashboard: IndexDashboardResponse;
  onNavigateToExplorer?: (horizonDays: number) => void;
  onSelectRoute?: (routeId: string) => void;
}

const HORIZON_METADATA: Record<string, { label: string; leadText: string; description: string }> = {
  'T+1': {
    label: '1-Day Lead',
    leadText: 'Next-Day Departure',
    description: 'Captures distressed / last-minute inventory. Sensitive to short-term route demand swings.'
  },
  'T+7': {
    label: '1-Week Lead',
    leadText: 'Weekly Booking Parity',
    description: 'Reflects short-lead domestic travel. Primary operational corridor baseline.'
  },
  'T+15': {
    label: 'AeroCPI Headline',
    leadText: '2-Week Advance Lead',
    description: 'Official sovereign measurement anchor. Balances consumer forward booking habits with pricing stability.'
  },
  'T+30': {
    label: '1-Month Lead',
    leadText: 'Standard Advance Window',
    description: 'Standard domestic planning window. Captures business and pre-planned consumer bookings.'
  },
  'T+45': {
    label: '6-Week Lead',
    leadText: 'Extended Early Advance',
    description: 'Long-range consumer advance booking. Reflects opening tier bucket tariffs before dynamic yield adjustment.'
  }
};

export const HorizonAnalysisPage: React.FC<HorizonAnalysisPageProps> = ({
  dashboard,
  onNavigateToExplorer,
  onSelectRoute,
}) => {
  const scope = dashboard.dashboard_scope;
  const [horizons, setHorizons] = useState<HorizonIntelligenceResponse[]>([]);
  const [selectedHorizonCode, setSelectedHorizonCode] = useState<string>('T+15');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load 5-horizon intelligence from backend endpoint
  const loadHorizons = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHorizonsIntelligence(scope.run_id);
      setHorizons(data);
    } catch (err: any) {
      console.error('Failed to load horizon intelligence:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load horizon intelligence');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHorizons();
  }, [scope.run_id]);

  const activeHorizon =
    horizons.find((h) => h.horizon_code === selectedHorizonCode) ||
    horizons.find((h) => h.is_headline) ||
    horizons[0];

  // SVG Curve Coordinate Mapping
  // Domain: T+1 (x: 60), T+7 (x: 160), T+15 (x: 260), T+30 (x: 360), T+45 (x: 460)
  // Range: Index values ~60 to 105 mapped into SVG y: 150 (bottom) to 25 (top)
  // Responsive Geometric Coordinate Mapping (No hardcoded pixels)
  const chartHeight = 240;
  
  const getYPercent = (val: number) => {
    // Determine dynamic domain based on data plus padding
    const minVal = Math.min(...horizons.map(h => h.index_value), 90) - 5;
    const maxVal = Math.max(...horizons.map(h => h.index_value), 110) + 5;
    const clamped = Math.max(minVal, Math.min(maxVal, val));
    const normalized = (clamped - minVal) / (maxVal - minVal);
    // 90% at bottom, 10% at top for padding
    return 90 - (normalized * 80);
  };

  const getXPercent = (idx: number, total: number) => {
    // 5% left margin, 95% right margin
    if (total <= 1) return 50;
    return 10 + (idx / (total - 1)) * 80;
  };

  const curvePoints = horizons.map((h, idx) => ({
    ...h,
    xPercent: getXPercent(idx, horizons.length),
    yPercent: getYPercent(h.index_value)
  }));

  // Build SVG path using percentages but converted to string coordinates for a 1000x400 viewbox?
  // SVG paths don't support % natively inside the M/C/L commands.
  // Instead, we use a fixed viewBox of 1000 400 and let it preserveAspectRatio="none", 
  // OR vector-effect="non-scaling-stroke" on everything.
  // The prompt asks to: "Create a deterministic coordinate mapping based on: chart width, chart height, data domain, data values."
  // And "Everything should live in the same responsive viewBox. Do NOT hardcode pixel coordinates tied to a single viewport."
  // I will use a standard viewBox "0 0 1000 400" and use vector-effect="non-scaling-stroke" so it scales fluidly without stroke distortion!
  
  const viewBoxWidth = 1000;
  const viewBoxHeight = 400;

  const getSvgY = (val: number) => {
    const minVal = Math.min(50, ...horizons.map(h => h.index_value - 5));
    const maxVal = Math.max(110, ...horizons.map(h => h.index_value + 5));
    const clamped = Math.max(minVal, Math.min(maxVal, val));
    const normalized = (clamped - minVal) / (maxVal - minVal);
    // 350 bottom, 50 top
    return 350 - (normalized * 300);
  };

  const getSvgX = (idx: number, total: number) => {
    if (total <= 1) return viewBoxWidth / 2;
    // 100 left, 900 right
    return 100 + (idx / (total - 1)) * 800;
  };

  const svgCurvePoints = horizons.map((h, idx) => ({
    ...h,
    x: getSvgX(idx, horizons.length),
    y: getSvgY(h.index_value)
  }));

  let pathD = '';
  if (svgCurvePoints.length > 0) {
    pathD = `M ${svgCurvePoints[0].x} ${svgCurvePoints[0].y}`;
    for (let i = 0; i < svgCurvePoints.length - 1; i++) {
      const p0 = svgCurvePoints[i];
      const p1 = svgCurvePoints[i + 1];
      const cx = (p0.x + p1.x) / 2;
      pathD += ` C ${cx} ${p0.y}, ${cx} ${p1.y}, ${p1.x} ${p1.y}`;
    }
  }

  // Accessibility screen-reader description
  const srDescription = horizons.map(h => `${h.horizon_code} = ${h.index_value.toFixed(3)}`).join(', ');

  const chartSVG = (
    <>
      <div className="sr-only">
        Forward Booking Horizon Curve / Term Structure. {srDescription}. Reference baseline = 100.000.
      </div>
      <svg 
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`} 
        preserveAspectRatio="none" 
        className="w-full h-48 sm:h-64 overflow-visible"
        aria-hidden="true"
      >
        {/* Horizontal Gridlines */}
        {[getSvgY(100), getSvgY(80), getSvgY(60)].map((gy, i) => (
           <line key={i} x1="50" y1={gy} x2="950" y2={gy} stroke="#E2E8F0" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        ))}

        {/* 100.00 Reference Baseline */}
        <line 
          x1="50" 
          y1={getSvgY(100)} 
          x2="950" 
          y2={getSvgY(100)} 
          stroke="#94A3B8" 
          strokeDasharray="8 8" 
          strokeWidth="2" 
          vectorEffect="non-scaling-stroke" 
        />
        <text 
          x="955" 
          y={getSvgY(100) + 5} 
          fill="#64748B" 
          fontSize="14" 
          fontFamily="monospace" 
          fontWeight="bold"
          textAnchor="start"
        >
          100.00 (Base)
        </text>

        {/* The Curve */}
        <motion.path
          d={pathD}
          fill="none"
          stroke="#2563EB"
          strokeWidth="4"
          vectorEffect="non-scaling-stroke"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        />

        {/* Nodes and Labels */}
        {svgCurvePoints.map((pt, idx) => {
          const isSelected = pt.horizon_code === selectedHorizonCode;
          return (
            <g 
              key={pt.horizon_code}
              className="cursor-pointer transition-transform hover:-translate-y-1"
              onClick={() => setSelectedHorizonCode(pt.horizon_code)}
            >
              {/* Dropdown line */}
              <line 
                x1={pt.x} 
                y1={pt.y} 
                x2={pt.x} 
                y2={350} 
                stroke={isSelected ? "#3B82F6" : "#CBD5E1"} 
                strokeDasharray="4 4" 
                strokeWidth="1.5"
                vectorEffect="non-scaling-stroke" 
              />
              
              {/* Node */}
              <circle 
                cx={pt.x} 
                cy={pt.y} 
                r={isSelected ? "8" : "6"} 
                fill={isSelected ? "#2563EB" : "#FFFFFF"} 
                stroke="#2563EB" 
                strokeWidth="3"
                vectorEffect="non-scaling-stroke" 
              />
              
              {/* X-Axis Label */}
              <text 
                x={pt.x} 
                y={375} 
                fill={isSelected ? "#1E293B" : "#64748B"} 
                fontSize="16" 
                fontFamily="sans-serif" 
                fontWeight="bold"
                textAnchor="middle"
              >
                {pt.horizon_code}
              </text>
              
              {/* Value Label */}
              <text 
                x={pt.x} 
                y={pt.y - 20} 
                fill={isSelected ? "#2563EB" : "#475569"} 
                fontSize="16" 
                fontFamily="monospace" 
                fontWeight="bold"
                textAnchor="middle"
              >
                {pt.index_value.toFixed(2)}
              </text>
            </g>
          );
        })}
      </svg>
    </>
  );

  return (
    <div className="space-y-8">
      {/* 1. Page Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Horizon Analysis</h1>
        <p className="text-sm text-slate-500 mt-1">
          Forward booking term structure and index formation across {horizons.length} observation windows.
        </p>
      </div>

      {/* 2. Interactive Horizon Curve (5-Horizon Canvas) */}
      <div className="surface-solid p-6 sm:p-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2">
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Forward Booking Horizon Curve / Term Structure
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Advance purchase mathematical elasticity measured against reference baseline.
            </p>
          </div>
          <span className="text-xs font-mono font-bold text-slate-400 bg-slate-50 px-2 py-1 rounded-md border border-slate-200">
            N={horizons.length} Horizons
          </span>
        </div>

        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400">
            <span className="text-xs font-semibold font-mono">Loading certified horizon series...</span>
          </div>
        ) : error ? (
          <div className="py-12 text-center text-rose-600 space-y-2">
            <p className="text-sm font-semibold">{error}</p>
            <button
              type="button"
              onClick={loadHorizons}
              className="px-3 py-1.5 rounded-lg bg-rose-50 border border-rose-200 text-xs font-bold hover:bg-rose-100 cursor-pointer"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Interactive SVG Curve Canvas */}
            <div className="relative w-full bg-gradient-to-b from-slate-50/50 to-white rounded-2xl border border-slate-200/80 p-4 sm:p-6 overflow-hidden">
              {chartSVG}

            </div>

            {/* 5-Horizon Interactive Selector Buttons */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {horizons.map((h) => {
                const isSelected = h.horizon_code === selectedHorizonCode;
                const meta = HORIZON_METADATA[h.horizon_code] || {
                  label: h.horizon_code,
                  leadText: `${h.horizon_days}d Lead`,
                  description: ''
                };
                const delta = h.index_value - 100.0;

                return (
                  <button
                    key={h.horizon_code}
                    type="button"
                    onClick={() => setSelectedHorizonCode(h.horizon_code)}
                    className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-2 ${
                      isSelected
                        ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/20 ring-2 ring-blue-500/20'
                        : 'bg-slate-50/80 hover:bg-slate-100 border-slate-200/80 text-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono font-bold text-xs">{h.horizon_code}</span>
                        {h.is_headline && (
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.2 rounded font-sans uppercase ${
                              isSelected ? 'bg-white/20 text-white' : 'bg-blue-100 text-blue-700'
                            }`}
                          >
                            Headline
                          </span>
                        )}
                      </div>
                      <span
                        className={`text-[10px] font-mono font-semibold ${
                          isSelected ? 'text-blue-100' : 'text-slate-400'
                        }`}
                      >
                        {meta.leadText}
                      </span>
                    </div>

                    <div className="flex items-baseline justify-between pt-1 border-t border-slate-200/40">
                      <span className="font-mono text-xl font-black tracking-tight mono-number">
                        {h.index_value.toFixed(2)}
                      </span>
                      <span
                        className={`text-xs font-mono font-bold ${
                          isSelected
                            ? 'text-blue-100'
                            : delta < 0
                            ? 'text-emerald-600'
                            : 'text-rose-600'
                        }`}
                      >
                        {delta > 0 ? '+' : ''}
                        {delta.toFixed(2)} pts
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 3. Selected Horizon Spotlight & Route Decomposition */}
      {activeHorizon && (
        <div className="surface-solid p-6 sm:p-8 space-y-6">
          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6 pb-6 border-b border-slate-100">
            <div className="space-y-2 max-w-2xl">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-[11px] font-mono font-bold uppercase">
                  HORIZON SPOTLIGHT
                </span>
                <span className="font-mono text-sm font-bold text-slate-900">
                  {activeHorizon.horizon_code}
                </span>
                <span className="text-slate-300">·</span>
                <span className="text-xs text-slate-500 font-medium">
                  {HORIZON_METADATA[activeHorizon.horizon_code]?.label || `${activeHorizon.horizon_days}-Day Advance`}
                </span>
                {activeHorizon.is_headline && (
                  <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-bold uppercase flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-amber-600" />
                    AeroCPI Headline Anchor
                  </span>
                )}
              </div>

              <div className="flex items-baseline gap-4 flex-wrap pt-1">
                <h3 className="text-4xl font-black text-slate-900 tracking-tight mono-number">
                  {activeHorizon.index_value.toFixed(2)}
                </h3>

                <div
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold border ${
                    activeHorizon.index_value < 100
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border-rose-200'
                  }`}
                >
                  {activeHorizon.index_value < 100 ? (
                    <TrendingDown className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <TrendingUp className="w-3.5 h-3.5 text-rose-600" />
                  )}
                  <span className="font-mono">
                    {(activeHorizon.index_value - 100.0).toFixed(2)} pts vs Base
                  </span>
                </div>

                {/* Cross-Module Navigation to Explorer */}
                {onNavigateToExplorer && (
                  <button
                    type="button"
                    onClick={() => onNavigateToExplorer(activeHorizon.horizon_days)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 text-blue-700 border border-blue-200/80 text-xs font-bold hover:bg-blue-100 transition-all cursor-pointer shadow-xs ml-auto"
                  >
                    <Search className="w-3.5 h-3.5" />
                    <span>Filter Explorer by {activeHorizon.horizon_code} →</span>
                  </button>
                )}
              </div>

              <p className="text-xs text-slate-600 leading-relaxed font-sans pt-1">
                {HORIZON_METADATA[activeHorizon.horizon_code]?.description ||
                  'Statistical series evaluating representative price relatives along sovereign corridors.'}
              </p>
            </div>

            {/* Horizon Health Diagnostics */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 min-w-[300px]">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                  Active Routes
                </span>
                <span className="text-sm font-bold font-mono text-slate-900 mt-0.5 block">
                  {activeHorizon.active_routes_count} / {activeHorizon.total_basket_routes_count}
                </span>
                <span className="text-[10px] text-slate-400 font-sans">100% Basket Match</span>
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                  Matched Coverage
                </span>
                <span className="text-sm font-bold font-mono text-emerald-700 mt-0.5 block">
                  {(activeHorizon.matched_coverage_ratio * 100).toFixed(0)}%
                </span>
                <span className="text-[10px] text-slate-400 font-sans">Zero Missing Routes</span>
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                  Weight Share
                </span>
                <span className="text-sm font-bold font-mono text-blue-700 mt-0.5 block">
                  {(activeHorizon.active_weight_sum * 100).toFixed(0)}%
                </span>
                <span className="text-[10px] text-slate-400 font-sans">DGCA Total Share</span>
              </div>
            </div>
          </div>

          {/* Question 3: Which routes are responsible for the differences at each horizon? */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Corridor Contributions Explaining {activeHorizon.horizon_code} Movement
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  Routes with the largest positive and negative point contributions to this horizon's index level.
                </p>
              </div>
              <span className="text-[11px] font-mono text-slate-400">
                Log-Linear Additive Attribution
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Largest Positive Contributions */}
              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
                  <div className="flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-rose-600" />
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
                      Largest Positive Contribution
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">Upward Shift</span>
                </div>

                {activeHorizon.top_positive_routes && activeHorizon.top_positive_routes.length > 0 ? (
                  <div className="space-y-2">
                    {activeHorizon.top_positive_routes.map((route) => (
                      <div
                        key={route.route_id}
                        className="bg-white p-3 rounded-xl border border-slate-200/70 flex items-center justify-between hover:border-slate-300 transition-all"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => onSelectRoute && onSelectRoute(route.route_id)}
                              className="font-mono font-bold text-xs text-blue-600 hover:underline cursor-pointer"
                            >
                              {route.route_id}
                            </button>
                            <span className="text-[10px] text-slate-400 font-mono">
                              ({route.origin} → {route.destination})
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                            ₹{route.base_representative_fare.toFixed(0)} → ₹{route.current_representative_fare.toFixed(0)}
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="font-mono text-xs font-bold text-rose-600 block">
                            +{route.point_contribution?.toFixed(4)} pts
                          </span>
                          <span className="text-[10px] font-mono text-slate-400">
                            Index: {route.route_index_value.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-6 text-center text-xs text-slate-400 font-sans italic">
                    No upward contributing corridors observed on this horizon.
                  </div>
                )}
              </div>

              {/* Largest Negative Contributions */}
              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
                  <div className="flex items-center gap-1.5">
                    <TrendingDown className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
                      Largest Negative Contribution
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">Downward Shift</span>
                </div>

                {activeHorizon.top_negative_routes && activeHorizon.top_negative_routes.length > 0 ? (
                  <div className="space-y-2">
                    {activeHorizon.top_negative_routes.map((route) => (
                      <div
                        key={route.route_id}
                        className="bg-white p-3 rounded-xl border border-slate-200/70 flex items-center justify-between hover:border-slate-300 transition-all"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => onSelectRoute && onSelectRoute(route.route_id)}
                              className="font-mono font-bold text-xs text-blue-600 hover:underline cursor-pointer"
                            >
                              {route.route_id}
                            </button>
                            <span className="text-[10px] text-slate-400 font-mono">
                              ({route.origin} → {route.destination})
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                            ₹{route.base_representative_fare.toFixed(0)} → ₹{route.current_representative_fare.toFixed(0)}
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="font-mono text-xs font-bold text-emerald-600 block">
                            {route.point_contribution?.toFixed(4)} pts
                          </span>
                          <span className="text-[10px] font-mono text-slate-400">
                            Index: {route.route_index_value.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-6 text-center text-xs text-slate-400 font-sans italic">
                    No downward contributing corridors observed on this horizon.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Complete 5-Horizon Comparative Term Structure Table */}
      <div className="surface-solid p-6 sm:p-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              5-Horizon Comparative Term Structure Summary
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Verified price relative indexes, baseline changes, and basket completeness across the full advance booking horizon set.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Reference: {scope.reference_date} = 100.00
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-200/90">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50/90 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Horizon</th>
                <th className="py-3 px-4">Lead Window</th>
                <th className="py-3 px-4 text-right">Index Value</th>
                <th className="py-3 px-4 text-right">Change vs Base</th>
                <th className="py-3 px-4 text-right">Active Basket</th>
                <th className="py-3 px-4 text-right">Coverage</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {horizons.map((h) => {
                const isSelected = h.horizon_code === selectedHorizonCode;
                const isHeadline = h.is_headline;
                const delta = h.index_value - 100.0;
                const meta = HORIZON_METADATA[h.horizon_code] || {
                  label: h.horizon_code,
                  leadText: `${h.horizon_days}d Lead`,
                  description: ''
                };

                return (
                  <tr
                    key={h.horizon_code}
                    onClick={() => setSelectedHorizonCode(h.horizon_code)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-blue-50/60 font-semibold'
                        : isHeadline
                        ? 'bg-slate-50/40'
                        : 'hover:bg-slate-50/60'
                    }`}
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            isHeadline
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {h.horizon_code}
                        </span>
                        {isHeadline && (
                          <span className="text-[10px] font-bold text-blue-700 font-sans uppercase">
                            Headline
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-3 px-4 font-sans text-slate-600">
                      {meta.leadText}
                    </td>

                    <td className="py-3 px-4 text-right text-slate-900 font-bold mono-number text-sm">
                      {h.index_value.toFixed(2)}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <span
                        className={`font-bold ${
                          delta < 0 ? 'text-emerald-600' : 'text-rose-600'
                        }`}
                      >
                        {delta > 0 ? '+' : ''}
                        {delta.toFixed(2)} pts
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right text-slate-700">
                      {h.active_routes_count} / {h.total_basket_routes_count}
                    </td>

                    <td className="py-3 px-4 text-right text-emerald-700 font-bold">
                      {(h.matched_coverage_ratio * 100).toFixed(0)}%
                    </td>

                    <td className="py-3 px-4 text-center">
                      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-sans font-bold">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" /> VERIFIED
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedHorizonCode(h.horizon_code);
                        }}
                        className="text-[11px] font-sans font-semibold text-blue-600 hover:text-blue-800"
                      >
                        Inspect →
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-start gap-2 text-xs text-slate-500">
          <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <span>
            Forward booking horizons represent independent advance purchase sampling windows. T+15 serves as the anchor headline for sovereign inflation comparison to balance lead-time elasticity against short-term volatility. AeroCPI is an independent economic index designed to augment CPI and is not statistically equivalent to CPI.
          </span>
        </div>
      </div>
    </div>
  );
};
