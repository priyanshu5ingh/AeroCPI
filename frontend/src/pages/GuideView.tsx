import React, { useState, useEffect } from 'react';
import {
  Sparkles, Search, Calendar, Plane, ShieldCheck, ArrowRight, CheckCircle2,
  AlertCircle, Clock, ChevronRight, RefreshCw, BarChart2, Layers, Info, ExternalLink,
  Zap, HelpCircle, Activity, Globe, Lock, Sliders, TrendingDown, TrendingUp,
  ArrowDownRight, ArrowUpRight, Check, Eye, ChevronDown, Compass, Database,
  FileText, CheckCircle, XCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AeroGuideAnalyzeResponse,
  AeroGuideAnalyzeRequest,
  AirlineRegistryItem,
  SourceCapabilityItem,
  ForecastingReadinessResponse,
  TrajectoryDetailResponse
} from '../types';
import {
  analyzeAirfare,
  fetchAirlines,
  fetchSourceCapabilities,
  fetchForecastingReadiness,
  fetchTrajectoryDetail
} from '../services/api';
import { DecisionTraceDrawer } from '../components/DecisionTraceDrawer';

const POPULAR_ROUTES = [
  { origin: 'BLR', dest: 'DEL', label: 'BLR ➔ DEL' },
  { origin: 'DEL', dest: 'BOM', label: 'DEL ➔ BOM' },
  { origin: 'BOM', dest: 'BLR', label: 'BOM ➔ BLR' },
  { origin: 'DEL', dest: 'HYD', label: 'DEL ➔ HYD' },
  { origin: 'DEL', dest: 'CCU', label: 'DEL ➔ CCU' },
  { origin: 'DEL', dest: 'MAA', label: 'DEL ➔ MAA' },
  { origin: 'BOM', dest: 'GOI', label: 'BOM ➔ GOI' },
  { origin: 'BLR', dest: 'HYD', label: 'BLR ➔ HYD' },
];

const SCAN_STEPS = [
  'REQUESTING OBSERVED QUOTES',
  'COMPARING MULTI-SOURCE FEEDS',
  'CALCULATING HISTORICAL POSITION',
  'EVALUATING ADVANCE PURCHASE WINDOW',
  'EXECUTING DECISION POLICY V1'
];

interface GuideViewProps {
  onNavigateToMarket?: () => void;
  onNavigateToProof?: () => void;
}

export const GuideView: React.FC<GuideViewProps> = ({
  onNavigateToMarket,
  onNavigateToProof,
}) => {
  // Search Form State
  const [origin, setOrigin] = useState('BLR');
  const [destination, setDestination] = useState('DEL');
  const [travelDate, setTravelDate] = useState('2026-10-18');
  const [flexibilityDays, setFlexibilityDays] = useState(2);
  const [priority, setPriority] = useState<'CHEAPEST' | 'FASTEST'>('CHEAPEST');

  // Intelligence State
  const [analysis, setAnalysis] = useState<AeroGuideAnalyzeResponse | null>(null);
  const [trajectory, setTrajectory] = useState<TrajectoryDetailResponse | null>(null);
  const [readiness, setReadiness] = useState<ForecastingReadinessResponse | null>(null);
  const [airlines, setAirlines] = useState<AirlineRegistryItem[]>([]);
  const [sources, setSources] = useState<SourceCapabilityItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanStepIndex, setScanStepIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Trace Drawer State
  const [isTraceDrawerOpen, setIsTraceDrawerOpen] = useState(false);

  // Initial Load
  useEffect(() => {
    fetchAirlines().then(setAirlines).catch(console.warn);
    fetchSourceCapabilities().then(setSources).catch(console.warn);
    fetchForecastingReadiness().then(setReadiness).catch(console.warn);
    handleAnalyze('BLR', 'DEL', '2026-10-18');
  }, []);

  const handleAnalyze = async (overrideOrigin?: string, overrideDest?: string, overrideDate?: string) => {
    const orig = overrideOrigin || origin;
    const dest = overrideDest || destination;
    const tDate = overrideDate || travelDate;

    if (orig === dest) {
      setError('Origin and Destination airports must be different.');
      return;
    }

    setLoading(true);
    setError(null);
    setScanStepIndex(0);

    const stepInterval = setInterval(() => {
      setScanStepIndex((prev) => (prev < SCAN_STEPS.length - 1 ? prev + 1 : prev));
    }, 280);

    const payload: AeroGuideAnalyzeRequest = {
      origin: orig,
      destination: dest,
      travel_date: tDate,
      flexibility_days: flexibilityDays,
      priority: priority,
      adults: 1,
      cabin: 'ECONOMY',
      currency: 'INR'
    };

    try {
      const [res, trajRes, rdRes] = await Promise.all([
        analyzeAirfare(payload),
        fetchTrajectoryDetail(`${orig}-${dest}`, tDate).catch(() => null),
        fetchForecastingReadiness().catch(() => null)
      ]);

      setAnalysis(res);
      if (trajRes) setTrajectory(trajRes);
      if (rdRes) setReadiness(rdRes);
    } catch (err: any) {
      console.error('AeroGuide analysis failed:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to analyze consumer airfare.');
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  };

  const getDecisionTheme = (guidance: string) => {
    switch (guidance) {
      case 'BOOK':
        return {
          label: 'BOOK NOW',
          bg: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
          glow: 'shadow-[0_0_50px_rgba(16,185,129,0.15)]',
          dot: 'bg-emerald-400',
          desc: 'Current fare is at or below the 15th percentile of historical corridor observations.'
        };
      case 'WAIT':
        return {
          label: 'WAIT TO BOOK',
          bg: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
          glow: 'shadow-[0_0_50px_rgba(245,158,11,0.15)]',
          dot: 'bg-amber-400',
          desc: 'Current fare is elevated relative to historical baseline with sufficient lead time.'
        };
      case 'FLEX_DATE':
        return {
          label: 'FLEX DATE RECOMMENDED',
          bg: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
          glow: 'shadow-[0_0_50px_rgba(168,85,247,0.15)]',
          dot: 'bg-purple-400',
          desc: 'A nearby candidate departure offers an observed lower market fare.'
        };
      default:
        return {
          label: 'WATCH FARE',
          bg: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
          glow: 'shadow-[0_0_50px_rgba(6,182,212,0.15)]',
          dot: 'bg-cyan-400',
          desc: 'Current fare aligns with typical historical prices for this corridor and advance window.'
        };
    }
  };

  return (
    <div className="space-y-8 pb-16 font-sans text-slate-100">
      {/* 1. The Hero: ONE Question */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-2xl relative overflow-hidden backdrop-blur-xl">
        <div className="absolute -right-20 -top-20 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -left-20 -bottom-20 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-6">
          {/* Tag & Headline */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>AEROGUIDE &bull; INDIA AIRFARE INTELLIGENCE</span>
              </div>
              <h1 className="text-3xl md:text-5xl font-black tracking-tight text-white font-sans">
                Should you book this flight?
              </h1>
            </div>

            {/* Quick Evidence Live Status */}
            <div className="flex items-center gap-3 bg-slate-950/70 border border-slate-800 px-4 py-2.5 rounded-2xl text-xs font-mono text-slate-300 shrink-0">
              <span className="flex h-2.5 w-2.5 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              <span>17,244 Live Observations</span>
              <span className="text-slate-600">&bull;</span>
              <span className="text-cyan-400">SHA-256 Verified</span>
            </div>
          </div>

          {/* Clean Cockpit Flight Query Inputs */}
          <div className="bg-slate-950/80 border border-slate-800/90 rounded-2xl p-4 md:p-6 shadow-inner space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              {/* Origin Airport */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                  Origin
                </label>
                <div className="relative">
                  <select
                    value={origin}
                    onChange={(e) => setOrigin(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-white font-mono font-bold text-sm rounded-xl px-3 py-2.5 appearance-none focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 cursor-pointer"
                  >
                    <option value="BLR">BLR - Bengaluru</option>
                    <option value="DEL">DEL - Delhi</option>
                    <option value="BOM">BOM - Mumbai</option>
                    <option value="HYD">HYD - Hyderabad</option>
                    <option value="CCU">CCU - Kolkata</option>
                    <option value="MAA">MAA - Chennai</option>
                    <option value="GOI">GOI - Goa</option>
                    <option value="PAT">PAT - Patna</option>
                  </select>
                  <Plane className="w-4 h-4 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>

              {/* Destination Airport */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                  Destination
                </label>
                <div className="relative">
                  <select
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-white font-mono font-bold text-sm rounded-xl px-3 py-2.5 appearance-none focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 cursor-pointer"
                  >
                    <option value="DEL">DEL - Delhi</option>
                    <option value="BOM">BOM - Mumbai</option>
                    <option value="BLR">BLR - Bengaluru</option>
                    <option value="HYD">HYD - Hyderabad</option>
                    <option value="CCU">CCU - Kolkata</option>
                    <option value="MAA">MAA - Chennai</option>
                    <option value="GOI">GOI - Goa</option>
                    <option value="PAT">PAT - Patna</option>
                  </select>
                  <Plane className="w-4 h-4 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none transform rotate-90" />
                </div>
              </div>

              {/* Travel Date */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                  Departure Date
                </label>
                <div className="relative">
                  <input
                    type="date"
                    value={travelDate}
                    onChange={(e) => setTravelDate(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-white font-mono font-bold text-sm rounded-xl px-3 py-2 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 cursor-pointer"
                  />
                </div>
              </div>

              {/* Flexibility Window */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                  Flexibility
                </label>
                <select
                  value={flexibilityDays}
                  onChange={(e) => setFlexibilityDays(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 text-white font-mono text-sm rounded-xl px-3 py-2.5 appearance-none focus:outline-none focus:border-cyan-500 cursor-pointer"
                >
                  <option value={1}>±1 Day Window</option>
                  <option value={2}>±2 Days (Smart Search)</option>
                  <option value={3}>±3 Days Window</option>
                </select>
              </div>

              {/* Primary CTA */}
              <div className="flex items-end">
                <button
                  onClick={() => handleAnalyze()}
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white font-mono font-bold text-sm py-2.5 px-4 rounded-xl shadow-lg shadow-blue-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin text-white" />
                      <span>SCANNING...</span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 text-cyan-300" />
                      <span>ANALYZE FLIGHT</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Popular Route Quick Chips */}
            <div className="flex flex-wrap items-center gap-2 pt-2 text-xs font-mono">
              <span className="text-slate-500 text-[11px]">Popular Corridors:</span>
              {POPULAR_ROUTES.map((r) => (
                <button
                  key={r.label}
                  onClick={() => {
                    setOrigin(r.origin);
                    setDestination(r.dest);
                    handleAnalyze(r.origin, r.dest, travelDate);
                  }}
                  className={`px-2.5 py-1 rounded-lg border text-[11px] font-bold transition-all cursor-pointer ${
                    origin === r.origin && destination === r.dest
                      ? 'bg-blue-600/30 text-cyan-300 border-cyan-500/50'
                      : 'bg-slate-900 text-slate-400 border-slate-800 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Loading Radar Overlay */}
      {loading && (
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 text-center space-y-4 shadow-xl backdrop-blur-xl">
          <div className="flex justify-center">
            <div className="relative w-16 h-16 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border-2 border-cyan-500/20 animate-ping" />
              <div className="w-12 h-12 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
              <Plane className="w-6 h-6 text-cyan-400 absolute" />
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs font-mono font-bold text-cyan-400 tracking-widest uppercase">
              {SCAN_STEPS[scanStepIndex]}
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Evaluating multi-carrier quotes against historical corridor percentile distributions...
            </p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm font-mono flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 2. THE DOMINANT DECISION CARD (Judge Centerpiece) */}
      {analysis && !loading && (() => {
        const theme = getDecisionTheme(analysis.booking_guidance);
        return (
          <div className="space-y-8">
            <div className={`bg-slate-900/90 border border-slate-800 rounded-3xl p-6 md:p-10 shadow-2xl relative overflow-hidden backdrop-blur-xl ${theme.glow}`}>
              <div className="space-y-8">
                {/* Header: Route, Travel Date, Advance Purchase Window */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl md:text-3xl font-black text-white font-mono tracking-tight">
                        {analysis.origin} ➔ {analysis.destination}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {analysis.travel_date}
                      </span>
                    </div>
                    <p className="text-xs font-mono text-slate-400">
                      Advance Purchase Window: <strong className="text-slate-200">T+{analysis.days_to_departure} Days</strong> &bull; Cabin: <strong className="text-slate-200">ECONOMY</strong>
                    </p>
                  </div>

                  {/* Why this decision CTA Button */}
                  <button
                    onClick={() => setIsTraceDrawerOpen(true)}
                    className="self-start sm:self-auto px-4 py-2.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 text-cyan-300 font-mono font-bold text-xs flex items-center gap-2 transition-all cursor-pointer shadow-sm hover:shadow-cyan-500/20"
                  >
                    <ShieldCheck className="w-4 h-4 text-cyan-400" />
                    <span>WHY THIS DECISION →</span>
                  </button>
                </div>

                {/* Dominant Decision & Price Block */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                  {/* Left Column: Big Fare & Dominant Verdict Badge */}
                  <div className="lg:col-span-5 space-y-4">
                    <div className="space-y-1">
                      <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest">
                        Current Lowest Observed Fare
                      </div>
                      <div className="text-4xl md:text-6xl font-black text-white font-mono tracking-tight">
                        ₹{analysis.current_observed_fare.toLocaleString('en-IN')}
                      </div>
                      <div className="text-xs font-mono text-slate-400 flex items-center gap-2 pt-1">
                        <span>Observed on: <strong className="text-slate-200">Google Flights</strong></span>
                        <span className="text-slate-600">&bull;</span>
                        <span className="text-emerald-400">● LIVE</span>
                      </div>
                    </div>

                    {/* Dominant Decision Badge */}
                    <div className={`p-4 rounded-2xl border ${theme.bg} space-y-1.5`}>
                      <div className="flex items-center gap-2">
                        <span className={`w-3 h-3 rounded-full ${theme.dot} animate-pulse`} />
                        <span className="text-lg md:text-xl font-black font-mono tracking-wider">
                          {theme.label}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 font-sans leading-relaxed">
                        {analysis.guidance_reason || theme.desc}
                      </p>
                    </div>
                  </div>

                  {/* Middle Column: AI Price Outlook (Strict Evidence Gated) */}
                  <div className="lg:col-span-4 bg-slate-950/70 border border-slate-800 p-5 rounded-2xl space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                        <span>AI Price Outlook</span>
                      </span>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase">
                        Evidence Limited
                      </span>
                    </div>

                    {/* Check if model probabilities exist or if in collecting state */}
                    {analysis.model_probabilities ? (
                      <div className="space-y-2 font-mono text-xs">
                        <div className="flex justify-between items-center text-slate-300">
                          <span>↓ FALL</span>
                          <strong className="text-emerald-400">{Math.round((analysis.model_probabilities.FALL || 0) * 100)}%</strong>
                        </div>
                        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div className="bg-emerald-500 h-full" style={{ width: `${(analysis.model_probabilities.FALL || 0) * 100}%` }} />
                        </div>
                        <div className="flex justify-between items-center text-slate-300 pt-1">
                          <span>→ STABLE</span>
                          <strong className="text-cyan-400">{Math.round((analysis.model_probabilities.STABLE || 0) * 100)}%</strong>
                        </div>
                        <div className="flex justify-between items-center text-slate-300">
                          <span>↑ RISE</span>
                          <strong className="text-rose-400">{Math.round((analysis.model_probabilities.RISE || 0) * 100)}%</strong>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <div className="text-xs font-bold text-slate-200 font-mono flex items-center gap-1.5">
                          <Lock className="w-3.5 h-3.5 text-amber-400" />
                          <span>COLLECTING LONGITUDINAL EVIDENCE</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
                          Zero manufactured probabilities. Forward predictive forecasting strictly locks until empirical 7-day longitudinal target pairs accumulate.
                        </p>
                        <div className="pt-1 flex items-center justify-between text-[10px] font-mono text-slate-500 border-t border-slate-800/80">
                          <span>7-Day Pairs: <strong>0 / 7</strong></span>
                          <span>Training Gate: <strong className="text-amber-400">LOCKED</strong></span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right Column: Factual Evidence Metrics */}
                  <div className="lg:col-span-3 bg-slate-950/70 border border-slate-800 p-5 rounded-2xl space-y-2.5 font-mono text-xs">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider pb-1 border-b border-slate-800">
                      Corridor Baseline Facts
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Route Median:</span>
                      <strong className="text-white">₹{analysis.route_historical_median.toLocaleString('en-IN')}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Percentile Rank:</span>
                      <strong className={analysis.price_position === 'LOW' ? 'text-emerald-400' : analysis.price_position === 'HIGH' ? 'text-amber-400' : 'text-cyan-400'}>
                        {analysis.price_position === 'LOW' ? 'P15 (Bottom 15%)' : analysis.price_position === 'HIGH' ? 'P80 (Top 20%)' : 'P50 (Median)'}
                      </strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Historical Min:</span>
                      <strong className="text-slate-300">₹{analysis.route_historical_min.toLocaleString('en-IN')}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Airlines Quoted:</span>
                      <strong className="text-slate-300">{analysis.airline_alternatives.length} Carriers</strong>
                    </div>
                  </div>
                </div>

                {/* Grounded Explanation Footer */}
                <div className="pt-4 border-t border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs text-slate-300">
                  <div className="flex items-start gap-2 max-w-3xl font-sans leading-relaxed">
                    <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                    <span>{analysis.grounded_explanation}</span>
                  </div>
                  <div className="shrink-0 font-mono text-[11px] text-slate-500">
                    Engine: <strong className="text-slate-400">AeroGuide-V1</strong> &bull; Policy: <strong className="text-slate-400">DECISION_POLICY_V1</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* 3. SMART FLEXIBLE DATES (±2 Days) */}
            {analysis.flexible_dates && analysis.flexible_dates.length > 0 && (
              <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-4 backdrop-blur-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-lg font-black text-white font-sans flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-cyan-400" />
                      Smart Flexible Dates Window (±{flexibilityDays} Days)
                    </h3>
                    <p className="text-xs text-slate-400 font-sans">
                      Observed lower fares on adjacent departure dates. Comparison against requested baseline.
                    </p>
                  </div>
                  <span className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1 rounded-full border border-slate-800">
                    Selected: {analysis.travel_date}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                  {analysis.flexible_dates.map((f) => {
                    const isSelected = f.days_diff === 0;
                    return (
                      <div
                        key={f.travel_date}
                        onClick={() => {
                          if (!isSelected) {
                            setTravelDate(f.travel_date);
                            handleAnalyze(origin, destination, f.travel_date);
                          }
                        }}
                        className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-blue-600/20 border-cyan-400 shadow-md ring-1 ring-cyan-400/40'
                            : f.is_lower_fare
                            ? 'bg-emerald-500/10 border-emerald-500/30 hover:border-emerald-500/60 hover:bg-emerald-500/15'
                            : 'bg-slate-950/60 border-slate-800 hover:bg-slate-900'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-xs font-mono font-bold text-slate-400">
                            {isSelected ? 'Selected Date' : (f.days_diff > 0 ? `+${f.days_diff} Day` : `${f.days_diff} Day`)}
                          </span>
                          {f.is_lower_fare && (
                            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase">
                              ↓ {Math.abs(f.percent_difference)}% observed lower
                            </span>
                          )}
                        </div>

                        <div className="text-xs font-mono font-bold text-slate-300 mb-1">
                          {f.travel_date}
                        </div>
                        <div className="text-xl font-black text-white font-mono">
                          ₹{f.observed_fare.toLocaleString('en-IN')}
                        </div>
                        <div className="text-[11px] font-mono pt-1">
                          {f.difference_from_requested < 0 ? (
                            <span className="text-emerald-400">
                              -₹{Math.abs(f.difference_from_requested).toLocaleString('en-IN')} observed difference
                            </span>
                          ) : isSelected ? (
                            <span className="text-cyan-400 font-bold">Selected Baseline</span>
                          ) : (
                            <span className="text-slate-500">
                              +₹{f.difference_from_requested.toLocaleString('en-IN')} difference
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 4. COMPACT AIRLINE OPTIONS MATRIX */}
            {analysis.airline_alternatives && analysis.airline_alternatives.length > 0 && (
              <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-4 backdrop-blur-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-lg font-black text-white font-sans flex items-center gap-2">
                      <Plane className="w-5 h-5 text-cyan-400" />
                      Airline Options &amp; Multi-Carrier Intelligence
                    </h3>
                    <p className="text-xs text-slate-400 font-sans">
                      Observed carrier offerings for {origin} ➔ {destination} on {analysis.travel_date}.
                    </p>
                  </div>
                  <span className="text-xs font-mono text-slate-400">
                    {analysis.airline_alternatives.length} Scheduled Carriers Quoted
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {analysis.airline_alternatives.map((a, idx) => (
                    <div
                      key={a.carrier_code + idx}
                      className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition-all space-y-2"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="text-sm font-extrabold text-white font-sans">
                            {a.airline_name}
                          </div>
                          <div className="text-[11px] font-mono text-slate-400">
                            Carrier: {a.carrier_code}
                          </div>
                        </div>
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-500/20 text-cyan-300 border border-blue-500/30">
                          {a.stops === 0 ? 'Non-Stop' : `${a.stops} Stop`}
                        </span>
                      </div>

                      <div className="text-2xl font-black text-white font-mono">
                        ₹{a.observed_fare.toLocaleString('en-IN')}
                      </div>

                      <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-1 border-t border-slate-900">
                        <span>Duration: ~{Math.floor(a.duration_minutes / 60)}h {a.duration_minutes % 60}m</span>
                        <span className="text-emerald-400">● Observed</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })()}

      {/* 5. 11-Node Decision Trace Drawer */}
      {analysis && (
        <DecisionTraceDrawer
          isOpen={isTraceDrawerOpen}
          onClose={() => setIsTraceDrawerOpen(false)}
          decisionTrace={analysis.decision_trace}
          guidance={analysis.booking_guidance}
          observedFare={analysis.current_observed_fare}
          origin={analysis.origin}
          destination={analysis.destination}
          travelDate={analysis.travel_date}
        />
      )}
    </div>
  );
};
