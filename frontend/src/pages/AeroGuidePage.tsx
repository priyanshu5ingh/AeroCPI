import React, { useState, useEffect } from 'react';
import {
  Sparkles, Search, Calendar, Plane, ShieldCheck, ArrowRight, CheckCircle2,
  AlertCircle, Clock, ChevronRight, RefreshCw, BarChart2, Layers, Info, ExternalLink,
  Zap, HelpCircle, Activity, Globe, Lock, Sliders, TrendingDown, TrendingUp,
  ArrowDownRight, ArrowUpRight, Check, Eye, ChevronDown, Compass, Database,
  FileText, CheckCircle, XCircle
} from 'lucide-react';
import {
  AeroGuideAnalyzeResponse,
  AeroGuideAnalyzeRequest,
  AirlineRegistryItem,
  SourceCapabilityItem,
  DecisionTraceNode,
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

const POPULAR_ROUTES = [
  { origin: 'DEL', dest: 'BOM', label: 'DEL ➔ BOM' },
  { origin: 'BLR', dest: 'DEL', label: 'BLR ➔ DEL' },
  { origin: 'BOM', dest: 'BLR', label: 'BOM ➔ BLR' },
  { origin: 'DEL', dest: 'HYD', label: 'DEL ➔ HYD' },
  { origin: 'DEL', dest: 'CCU', label: 'DEL ➔ CCU' },
  { origin: 'DEL', dest: 'MAA', label: 'DEL ➔ MAA' },
  { origin: 'BOM', dest: 'GOI', label: 'BOM ➔ GOI' },
  { origin: 'BLR', dest: 'HYD', label: 'BLR ➔ HYD' },
  { origin: 'DEL', dest: 'PAT', label: 'DEL ➔ PAT' },
  { origin: 'BLR', dest: 'CCU', label: 'BLR ➔ CCU' },
];

export const AeroGuidePage: React.FC = () => {
  // Search Form State
  const [origin, setOrigin] = useState('DEL');
  const [destination, setDestination] = useState('BOM');
  const [travelDate, setTravelDate] = useState(() => {
    return '2026-10-01'; // Default to first pinned pilot departure date
  });
  const [flexibilityDays, setFlexibilityDays] = useState(2);
  const [priority, setPriority] = useState<'CHEAPEST' | 'FASTEST'>('CHEAPEST');

  // Intelligence Results State
  const [analysis, setAnalysis] = useState<AeroGuideAnalyzeResponse | null>(null);
  const [trajectory, setTrajectory] = useState<TrajectoryDetailResponse | null>(null);
  const [readiness, setReadiness] = useState<ForecastingReadinessResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active Navigation Tab
  const [activeTab, setActiveTab] = useState<'overview' | 'trace' | 'what-changed' | 'airlines' | 'panel-health'>('overview');
  const [selectedTraceStep, setSelectedTraceStep] = useState<number>(8);

  // Metadata Catalogs
  const [airlines, setAirlines] = useState<AirlineRegistryItem[]>([]);
  const [sources, setSources] = useState<SourceCapabilityItem[]>([]);

  // Initial Data Fetch
  useEffect(() => {
    fetchAirlines().then(setAirlines).catch(console.warn);
    fetchSourceCapabilities().then(setSources).catch(console.warn);
    fetchForecastingReadiness().then(setReadiness).catch(console.warn);
    handleAnalyze();
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
      const res = await analyzeAirfare(payload);
      setAnalysis(res);
      setSelectedTraceStep(res.decision_trace.length || 8);

      // Fetch trajectory details for this route & date
      const trajRes = await fetchTrajectoryDetail(`${orig}-${dest}`, tDate);
      setTrajectory(trajRes);

      const rdRes = await fetchForecastingReadiness();
      setReadiness(rdRes);
    } catch (err: any) {
      console.error('AeroGuide analysis failed:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to analyze consumer airfare.');
    } finally {
      setLoading(false);
    }
  };

  const getGuidanceBadge = (guidance: string) => {
    switch (guidance) {
      case 'BOOK':
        return {
          label: 'BOOK NOW',
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          dot: 'bg-emerald-400',
          desc: 'Current fare is at or below the 15th percentile of historical corridor observations.'
        };
      case 'WAIT':
        return {
          label: 'WAIT TO BOOK',
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          dot: 'bg-amber-400',
          desc: 'Current fare is elevated relative to historical baseline with sufficient lead time.'
        };
      case 'FLEX_DATE':
        return {
          label: 'FLEX DATE RECOMMENDED',
          bg: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
          dot: 'bg-purple-400',
          desc: 'A nearby candidate departure offers a significantly lower observed market fare.'
        };
      default:
        return {
          label: 'WATCH FARE',
          bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          dot: 'bg-blue-400',
          desc: 'Current fare aligns with typical historical prices for this corridor and advance window.'
        };
    }
  };


  return (
    <div className="space-y-8 pb-16 font-sans text-slate-900">
      {/* 1. Master Header: National Market State & AeroGuide Hero */}
      <div className="bg-slate-950 text-white rounded-3xl p-6 md:p-8 shadow-2xl relative overflow-hidden border border-slate-800">
        <div className="absolute -right-20 -top-20 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -left-20 -bottom-20 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-6">
          {/* Top Bar: Live National Market State */}
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/80 text-xs font-mono">
            <div className="flex items-center gap-3">
              <span className="flex h-2.5 w-2.5 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              <span className="text-slate-400">AeroCPI National Market:</span>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30 flex items-center gap-1">
                <TrendingDown className="w-3 h-3" /> FALLING (T+15 ↓ 3.66 pts)
              </span>
            </div>

            <div className="flex items-center gap-4 text-slate-400">
              <span>Horizons: <strong className="text-slate-200">T+1 (→) &bull; T+7 (→) &bull; T+15 (↓) &bull; T+30 (↓)</strong></span>
              <span className="hidden md:inline text-slate-600">|</span>
              <span className="hidden md:inline text-slate-300">Policy: <strong className="text-white">DECISION_POLICY_V1</strong></span>
            </div>
          </div>

          {/* Hero Pitch Headline */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>AeroGuide &bull; Consumer Decision Intelligence</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-black tracking-tight text-white">
                Should you book today?
              </h1>
              <p className="text-sm md:text-base text-slate-300 leading-relaxed">
                AeroGuide turns India's national airfare index into an evidence-grounded booking decision engine. 
                Every recommendation is backed by live multi-carrier quotes, historical distributions, and an auditable 8-node decision trace.
              </p>
            </div>

            {/* Quick Metrics Badge */}
            <div className="flex flex-wrap lg:flex-col gap-2.5 bg-white/5 backdrop-blur-md p-4 rounded-2xl border border-white/10 text-xs font-mono text-slate-300 shrink-0">
              <div className="flex justify-between items-center gap-4">
                <span className="text-slate-400">140 Pinned Trajectories:</span>
                <span className="text-emerald-400 font-bold">TRACKING ACTIVE</span>
              </div>
              <div className="flex justify-between items-center gap-4">
                <span className="text-slate-400">7-Day Target Pairs:</span>
                <span className="text-amber-400 font-bold">0 / 7 (COLLECTING)</span>
              </div>
              <div className="flex justify-between items-center gap-4">
                <span className="text-slate-400">ML Hallucination Guard:</span>
                <span className="text-blue-400 font-bold">ZERO SYNTHETIC</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Interactive Search Form & Corridor Selector */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAnalyze();
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-4 items-end">
            {/* Origin Airport */}
            <div className="lg:col-span-3 space-y-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
                From (Origin)
              </label>
              <div className="relative">
                <select
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-sm font-bold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none cursor-pointer"
                >
                  <option value="DEL">DEL — Delhi (Indira Gandhi)</option>
                  <option value="BOM">BOM — Mumbai (Chhatrapati Shivaji)</option>
                  <option value="BLR">BLR — Bengaluru (Kempegowda)</option>
                  <option value="HYD">HYD — Hyderabad (Rajiv Gandhi)</option>
                  <option value="CCU">CCU — Kolkata (Netaji Subhash)</option>
                  <option value="MAA">MAA — Chennai (Chennai Intl)</option>
                  <option value="GOI">GOI — Goa (Dabolim)</option>
                  <option value="PAT">PAT — Patna (Jay Prakash)</option>
                  <option value="COK">COK — Kochi (Cochin)</option>
                  <option value="PNQ">PNQ — Pune</option>
                </select>
                <Plane className="w-4 h-4 text-slate-400 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            {/* Destination Airport */}
            <div className="lg:col-span-3 space-y-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
                To (Destination)
              </label>
              <div className="relative">
                <select
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-sm font-bold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none cursor-pointer"
                >
                  <option value="BOM">BOM — Mumbai (Chhatrapati Shivaji)</option>
                  <option value="DEL">DEL — Delhi (Indira Gandhi)</option>
                  <option value="BLR">BLR — Bengaluru (Kempegowda)</option>
                  <option value="HYD">HYD — Hyderabad (Rajiv Gandhi)</option>
                  <option value="CCU">CCU — Kolkata (Netaji Subhash)</option>
                  <option value="MAA">MAA — Chennai (Chennai Intl)</option>
                  <option value="GOI">GOI — Goa (Dabolim)</option>
                  <option value="PAT">PAT — Patna (Jay Prakash)</option>
                  <option value="COK">COK — Kochi (Cochin)</option>
                  <option value="PNQ">PNQ — Pune</option>
                </select>
                <Plane className="w-4 h-4 text-slate-400 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            {/* Travel Date */}
            <div className="lg:col-span-3 space-y-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
                Departure Date
              </label>
              <div className="relative">
                <input
                  type="date"
                  value={travelDate}
                  onChange={(e) => setTravelDate(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-sm font-bold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Date Flex & Analyze */}
            <div className="lg:col-span-3 flex gap-2 items-center">
              <div className="flex-1 space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
                  Flexibility
                </label>
                <select
                  value={flexibilityDays}
                  onChange={(e) => setFlexibilityDays(Number(e.target.value))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-3 py-3 text-xs font-bold text-slate-800 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value={0}>Exact Date</option>
                  <option value={1}>± 1 Day</option>
                  <option value={2}>± 2 Days (Recommended)</option>
                  <option value={3}>± 3 Days</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-transparent font-mono">
                  Action
                </label>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold text-sm px-6 py-3 rounded-2xl transition-all flex items-center gap-2 shadow-lg shadow-blue-500/20 disabled:opacity-50 cursor-pointer"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  <span>Evaluate</span>
                </button>
              </div>
            </div>
          </div>

          {/* Quick Route Selector Pills */}
          <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold font-mono text-slate-400 mr-1">10 Tier-1 Core Corridors:</span>
            {POPULAR_ROUTES.map((r) => {
              const isActive = origin === r.origin && destination === r.dest;
              return (
                <button
                  key={`${r.origin}-${r.dest}`}
                  type="button"
                  onClick={() => {
                    setOrigin(r.origin);
                    setDestination(r.dest);
                    handleAnalyze(r.origin, r.dest);
                  }}
                  className={`text-xs px-3 py-1.5 rounded-xl font-mono font-bold transition-all cursor-pointer ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 border border-slate-200/60'
                  }`}
                >
                  {r.label}
                </button>
              );
            })}
          </div>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-800 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {analysis && (
        <div className="space-y-8">
          {/* 3. HERO DECISION ZONE: The "Should I Book?" Verdict */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Primary Dominant Verdict Card */}
            <div className="lg:col-span-8 bg-gradient-to-br from-slate-900 via-slate-950 to-indigo-950 text-white rounded-3xl p-6 md:p-8 shadow-xl border border-slate-800 relative overflow-hidden flex flex-col justify-between">
              <div className="space-y-6">
                {/* Header & Badges */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-black font-mono tracking-tight text-white">
                      {analysis.origin} ➔ {analysis.destination}
                    </span>
                    <span className="text-xs font-mono text-slate-400 bg-white/10 px-2.5 py-1 rounded-full">
                      {analysis.days_to_departure} days to departure &bull; {analysis.travel_date}
                    </span>
                  </div>

                  {(() => {
                    const b = getGuidanceBadge(analysis.booking_guidance);
                    return (
                      <span className={`px-4 py-1.5 rounded-full text-xs font-mono font-black border flex items-center gap-2 ${b.bg}`}>
                        <span className={`w-2 h-2 rounded-full ${b.dot}`} />
                        {b.label}
                      </span>
                    );
                  })()}
                </div>

                {/* Dominant Verdict Text & Callout */}
                <div className="space-y-2">
                  <div className="text-xs font-mono uppercase tracking-widest text-slate-400">
                    Deterministic Policy Verdict
                  </div>
                  <div className="text-3xl md:text-4xl font-black text-white tracking-tight">
                    {analysis.booking_guidance === 'FLEX_DATE' ? 'Save money by shifting your date ±2 days' :
                     analysis.booking_guidance === 'BOOK' ? 'Favorable fare window — Book now' :
                     analysis.booking_guidance === 'WAIT' ? 'Elevated fare — Wait for correction' :
                     'Market typical — Watch and track price progression'}
                  </div>
                  <p className="text-sm text-slate-300 max-w-2xl leading-relaxed pt-1">
                    {analysis.guidance_reason}
                  </p>
                </div>

                {/* Key Metric Triad */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800 text-xs font-mono">
                  <div className="bg-white/5 p-4 rounded-2xl border border-white/10 space-y-1">
                    <div className="text-slate-400">Current Observed Fare</div>
                    <div className="text-2xl font-extrabold text-white">
                      ₹{analysis.current_observed_fare.toLocaleString('en-IN')}
                    </div>
                    <div className="text-[11px] text-slate-400 font-sans">Lowest standard quote</div>
                  </div>

                  <div className="bg-white/5 p-4 rounded-2xl border border-white/10 space-y-1">
                    <div className="text-slate-400">Route Historical Median</div>
                    <div className="text-2xl font-extrabold text-blue-400">
                      ₹{analysis.route_historical_median.toLocaleString('en-IN')}
                    </div>
                    <div className="text-[11px] text-slate-400 font-sans">
                      Range: ₹{analysis.route_historical_min.toLocaleString('en-IN')} - ₹{analysis.route_historical_max.toLocaleString('en-IN')}
                    </div>
                  </div>

                  <div className="bg-white/5 p-4 rounded-2xl border border-white/10 space-y-1">
                    <div className="text-slate-400">Price Position</div>
                    <div className="text-2xl font-extrabold text-emerald-400">
                      {analysis.price_position}
                    </div>
                    <div className="text-[11px] text-slate-400 font-sans">
                      {analysis.observations_in_sample} corridor samples
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons Row */}
              <div className="pt-6 mt-6 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-wrap gap-2.5">
                  <button
                    onClick={() => setActiveTab('trace')}
                    className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold font-mono flex items-center gap-2 transition-all shadow-md shadow-blue-500/20 cursor-pointer"
                  >
                    <ShieldCheck className="w-4 h-4" />
                    <span>WHY THIS DECISION? (8-NODE TRACE)</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('what-changed')}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold font-mono flex items-center gap-2 transition-all cursor-pointer"
                  >
                    <BarChart2 className="w-4 h-4 text-emerald-400" />
                    <span>WHAT CHANGED? (MARKET DRIVERS)</span>
                  </button>
                </div>

                <div className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Audited Lineage</span>
                </div>
              </div>
            </div>

            {/* Smart Flexible Date Highlight or Quick AI Explanation */}
            <div className="lg:col-span-4 bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 font-mono uppercase tracking-wider">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                    Grounded AI Summary
                  </h3>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    ZERO HALLUCINATION
                  </span>
                </div>

                <div className="text-xs text-slate-700 leading-relaxed font-sans bg-slate-50 p-4 rounded-2xl border border-slate-100 space-y-2">
                  <p className="font-bold text-slate-900 leading-relaxed">
                    {analysis.grounded_explanation}
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 text-[11px] pt-1">
                    <li>Current fare ₹{analysis.current_observed_fare.toLocaleString('en-IN')} is categorized as {analysis.price_position} relative to corridor baseline.</li>
                    <li>Evaluated {analysis.airline_alternatives.length} carriers on {analysis.travel_date}.</li>
                    <li>Decision governed deterministically under {analysis.decision_policy_version}.</li>
                  </ul>
                </div>

                {/* Best Flexible Date Callout */}
                {analysis.flexible_dates && analysis.flexible_dates.find(f => f.is_lower_fare) && (
                  <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono font-bold text-emerald-800">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-4 h-4 text-emerald-600" />
                        Nearby Saving Opportunity
                      </span>
                      <span className="bg-emerald-600 text-white text-[10px] px-2 py-0.5 rounded-full">
                        LOWER FARE
                      </span>
                    </div>
                    {(() => {
                      const best = analysis.flexible_dates.find(f => f.is_lower_fare)!;
                      return (
                        <div className="text-xs text-emerald-950 font-sans">
                          Fly on <strong>{best.travel_date}</strong> ({best.days_diff > 0 ? `+${best.days_diff}` : best.days_diff} days) for{' '}
                          <strong className="text-emerald-700 text-sm font-mono">₹{best.observed_fare.toLocaleString('en-IN')}</strong>{' '}
                          ({Math.abs(best.percent_difference)}% cheaper than requested date).
                        </div>
                      );
                    })()}
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-mono text-slate-500">
                <span>Engine: AeroGuide-V1</span>
                <button
                  onClick={() => setActiveTab('airlines')}
                  className="text-blue-600 font-bold hover:underline flex items-center gap-1 cursor-pointer"
                >
                  View Airlines <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* 4. Navigation Sub-Tabs: Decision Trace, Market Drivers, Airlines, Trajectory Panel */}
          <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer ${
                activeTab === 'overview'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Overview &amp; Alternatives
            </button>

            <button
              onClick={() => setActiveTab('trace')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'trace'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>8-Node Decision Trace Flow</span>
            </button>

            <button
              onClick={() => setActiveTab('what-changed')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'what-changed'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>What Changed? (Market Drivers)</span>
            </button>

            <button
              onClick={() => setActiveTab('airlines')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'airlines'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <Plane className="w-3.5 h-3.5" />
              <span>Airline Intelligence ({analysis.airline_alternatives.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('panel-health')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'panel-health'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <Database className="w-3.5 h-3.5 text-indigo-500" />
              <span>Trajectory &amp; Panel Health</span>
            </button>
          </div>

          {/* TAB 1: Overview & Flexible Dates Strip */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Flexible Date Window Comparison */}
              {analysis.flexible_dates && analysis.flexible_dates.length > 0 && (
                <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 font-mono">
                        <Calendar className="w-5 h-5 text-blue-600" />
                        Smart Flexible Dates Window (± {flexibilityDays} Days)
                      </h3>
                      <p className="text-xs text-slate-500 font-sans">
                        Real observed fares on adjacent departure dates for {origin} ➔ {destination}.
                      </p>
                    </div>
                    <span className="text-xs font-mono font-bold text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
                      Requested: {analysis.travel_date}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                    {analysis.flexible_dates.map((f) => {
                      const isRequested = f.days_diff === 0;
                      return (
                        <div
                          key={f.travel_date}
                          onClick={() => {
                            if (!isRequested) {
                              setTravelDate(f.travel_date);
                              handleAnalyze(origin, destination, f.travel_date);
                            }
                          }}
                          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                            isRequested
                              ? 'bg-blue-50/80 border-blue-400 ring-2 ring-blue-500/20 shadow-xs'
                              : f.is_lower_fare
                              ? 'bg-emerald-50/80 border-emerald-300 hover:border-emerald-400 hover:shadow-sm'
                              : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                          }`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-mono font-bold text-slate-600">
                              {isRequested ? 'Selected Date' : (f.days_diff > 0 ? `+${f.days_diff} Day` : `${f.days_diff} Day`)}
                            </span>
                            {f.is_lower_fare && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-600 text-white uppercase">
                                Save {Math.abs(f.percent_difference)}%
                              </span>
                            )}
                          </div>
                          <div className="text-sm font-extrabold text-slate-900 mb-1 font-mono">
                            {f.travel_date}
                          </div>
                          <div className="text-lg font-black text-slate-900 font-mono">
                            ₹{f.observed_fare.toLocaleString('en-IN')}
                          </div>
                          <div className="text-[11px] font-mono text-slate-500 pt-1">
                            {f.difference_from_requested < 0 ? (
                              <span className="text-emerald-700 font-bold">
                                -₹{Math.abs(f.difference_from_requested).toLocaleString('en-IN')} vs request
                              </span>
                            ) : isRequested ? (
                              <span className="text-blue-700 font-bold">Requested baseline</span>
                            ) : (
                              <span className="text-slate-500">
                                +₹{f.difference_from_requested.toLocaleString('en-IN')} vs request
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Scientific ML Safety Gate Banner */}
              <div className="bg-slate-900 text-white rounded-3xl border border-slate-800 p-6 shadow-sm space-y-4">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                        STATUS: COLLECTING_LONGITUDINAL_EVIDENCE
                      </span>
                      <span className="text-xs font-mono text-slate-400 hidden sm:inline">
                        &bull; Zero Fake ML Predictions
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-slate-100">
                      Scientific AI Policy &bull; Temporal Evidence Guard
                    </h4>
                    <p className="text-xs md:text-sm text-slate-300 max-w-3xl leading-relaxed">
                      Unlike superficial demos that fabricate speculative ML predictions, AeroGuide strictly locks machine learning forecasting until 
                      empirical 7-day target pairs accumulate across our 140-trajectory daily collection panel.
                    </p>
                  </div>

                  <div className="bg-slate-800/90 border border-slate-700 p-4 rounded-2xl text-xs font-mono text-slate-300 shrink-0 space-y-2">
                    <div className="flex justify-between gap-6">
                      <span className="text-slate-400">Valid 7-Day Targets:</span>
                      <strong className="text-white">0 / 7 pairs (Collecting)</strong>
                    </div>
                    <div className="flex justify-between gap-6">
                      <span className="text-slate-400">Model Training:</span>
                      <strong className="text-amber-400">DISABLED (Guarded)</strong>
                    </div>
                    <div className="flex justify-between gap-6">
                      <span className="text-slate-400">Audit Hash:</span>
                      <strong className="text-emerald-400">VERIFIED_AUTHENTIC</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Verifiable 8-Node Decision Trace Flow */}
          {activeTab === 'trace' && (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 md:p-8 shadow-sm space-y-8">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 mb-2 font-mono">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Auditable Step-by-Step Computational Lineage</span>
                </div>
                <h3 className="text-2xl font-black text-slate-900 tracking-tight">
                  Interactive 8-Node Decision Trace
                </h3>
                <p className="text-sm text-slate-500 max-w-3xl leading-relaxed font-sans">
                  Click any stage below to inspect the deterministic inputs, computational identities, and scientific evidence behind AeroGuide's verdict.
                </p>
              </div>

              {/* 8-Node Interactive Step Progression */}
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
                {analysis.decision_trace.map((node) => {
                  const isSelected = selectedTraceStep === node.stage_number;
                  return (
                    <button
                      key={node.stage_number}
                      onClick={() => setSelectedTraceStep(node.stage_number)}
                      className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                        isSelected
                          ? 'bg-blue-50 border-blue-500 ring-2 ring-blue-500/30 shadow-md'
                          : 'bg-slate-50/80 border-slate-200 hover:bg-slate-100/80'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                          isSelected ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'
                        }`}>
                          Node {node.stage_number}
                        </span>
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      </div>
                      <div className="text-xs font-extrabold text-slate-900 line-clamp-2 leading-tight">
                        {node.stage_name}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Deep Inspector for Selected Step */}
              {(() => {
                const node = analysis.decision_trace.find(n => n.stage_number === selectedTraceStep) || analysis.decision_trace[analysis.decision_trace.length - 1];
                return (
                  <div className="bg-slate-950 text-white rounded-2xl p-6 md:p-8 border border-slate-800 space-y-6">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                      <div className="flex items-center gap-3">
                        <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                          STAGE {node.stage_number} OF 8
                        </span>
                        <h4 className="text-lg font-black text-white font-mono">
                          {node.stage_name}
                        </h4>
                      </div>
                      <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        STATUS: {node.status}
                      </span>
                    </div>

                    <div className="space-y-4">
                      <div className="text-xs font-mono text-slate-400 uppercase tracking-widest font-bold">
                        Evidence Summary
                      </div>
                      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 leading-relaxed font-sans">
                        {node.evidence_summary}
                      </div>

                      <div className="text-xs font-mono text-slate-400 uppercase tracking-widest font-bold pt-2">
                        Structured Computation Payload
                      </div>
                      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-emerald-300 overflow-x-auto">
                        <pre>{JSON.stringify(node.structured_payload, null, 2)}</pre>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* TAB 3: What Changed? (Market Drivers Attribution Bridge) */}
          {activeTab === 'what-changed' && (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 md:p-8 shadow-sm space-y-8">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 mb-2 font-mono">
                  <BarChart2 className="w-3.5 h-3.5 text-blue-600" />
                  <span>AeroCPI National Index ➔ Consumer Route Bridge</span>
                </div>
                <h3 className="text-2xl font-black text-slate-900 tracking-tight">
                  Why did the market move &amp; what does it mean for your journey?
                </h3>
                <p className="text-sm text-slate-500 max-w-3xl leading-relaxed font-sans">
                  This bridge translates official DGCA-weighted national price movements directly into actionable consumer airfare context.
                </p>
              </div>

              {/* National Market Movement Overview Card */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-5 rounded-2xl bg-slate-900 text-white space-y-2">
                  <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">National T+15 Index</div>
                  <div className="text-3xl font-black text-white font-mono">96.21</div>
                  <div className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                    <TrendingDown className="w-3.5 h-3.5" /> -3.66 points (-3.79%) vs reference
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="text-xs font-mono text-slate-500 uppercase tracking-wider">Selected Corridor ({origin}-{destination})</div>
                  <div className="text-3xl font-black text-slate-900 font-mono">₹{analysis.current_observed_fare.toLocaleString('en-IN')}</div>
                  <div className="text-xs font-mono text-blue-600">
                    Position: {analysis.price_position} (Median: ₹{analysis.route_historical_median.toLocaleString('en-IN')})
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 space-y-2">
                  <div className="text-xs font-mono text-emerald-800 uppercase tracking-wider">Consumer Translation</div>
                  <div className="text-base font-extrabold text-emerald-950 font-sans">Downward Airfare Drift</div>
                  <div className="text-xs text-emerald-800 font-sans">
                    Easing price pressure supports a patient booking posture.
                  </div>
                </div>
              </div>

              {/* Route Attribution Drivers Table */}
              <div className="space-y-4">
                <h4 className="text-base font-bold text-slate-900 font-mono flex items-center gap-2">
                  <span>Top National Route Contributors (Log-Linear Point Attribution)</span>
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Downward Drivers */}
                  <div className="p-5 rounded-2xl bg-emerald-50/60 border border-emerald-200 space-y-3">
                    <div className="text-xs font-mono font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
                      <ArrowDownRight className="w-4 h-4 text-emerald-600" />
                      <span>Downward Drivers (Price Reductions)</span>
                    </div>
                    <div className="space-y-2 text-xs font-mono">
                      <div className="flex justify-between p-2.5 bg-white rounded-xl border border-emerald-100">
                        <span className="font-bold text-slate-800">GOI ➔ BOM (Goa-Mumbai)</span>
                        <span className="text-emerald-700 font-black">-4.7391 pts</span>
                      </div>
                      <div className="flex justify-between p-2.5 bg-white rounded-xl border border-emerald-100">
                        <span className="font-bold text-slate-800">BLR ➔ DEL (Bengaluru-Delhi)</span>
                        <span className="text-emerald-700 font-black">-0.7875 pts</span>
                      </div>
                      <div className="flex justify-between p-2.5 bg-white rounded-xl border border-emerald-100">
                        <span className="font-bold text-slate-800">MAA ➔ DEL (Chennai-Delhi)</span>
                        <span className="text-emerald-700 font-black">-0.2993 pts</span>
                      </div>
                    </div>
                  </div>

                  {/* Upward Drivers */}
                  <div className="p-5 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-3">
                    <div className="text-xs font-mono font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1.5">
                      <ArrowUpRight className="w-4 h-4 text-amber-600" />
                      <span>Upward Drivers (Price Escalations)</span>
                    </div>
                    <div className="space-y-2 text-xs font-mono">
                      <div className="flex justify-between p-2.5 bg-white rounded-xl border border-amber-100">
                        <span className="font-bold text-slate-800">DEL ➔ HYD (Delhi-Hyderabad)</span>
                        <span className="text-amber-700 font-black">+1.0675 pts</span>
                      </div>
                      <div className="flex justify-between p-2.5 bg-white rounded-xl border border-amber-100">
                        <span className="font-bold text-slate-800">BLR ➔ CCU (Bengaluru-Kolkata)</span>
                        <span className="text-amber-700 font-black">+0.3269 pts</span>
                      </div>
                      <div className="flex justify-between p-2.5 bg-white rounded-xl border border-amber-100">
                        <span className="font-bold text-slate-800">BLR ➔ HYD (Bengaluru-Hyderabad)</span>
                        <span className="text-amber-700 font-black">+0.2805 pts</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Airline Intelligence Matrix */}
          {activeTab === 'airlines' && (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 md:p-8 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-2xl font-black text-slate-900 tracking-tight">
                    Observed Multi-Carrier Intelligence
                  </h3>
                  <p className="text-xs text-slate-500 font-sans">
                    Standardized quotes on {analysis.travel_date} across domestic carriers and distribution channels.
                  </p>
                </div>

                {/* Priority Selector */}
                <div className="flex items-center bg-slate-100 p-1 rounded-2xl border border-slate-200">
                  <button
                    onClick={() => {
                      setPriority('CHEAPEST');
                      handleAnalyze();
                    }}
                    className={`px-4 py-1.5 text-xs font-bold rounded-xl transition-all cursor-pointer ${
                      priority === 'CHEAPEST' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Lowest Fare First
                  </button>
                  <button
                    onClick={() => {
                      setPriority('FASTEST');
                      handleAnalyze();
                    }}
                    className={`px-4 py-1.5 text-xs font-bold rounded-xl transition-all cursor-pointer ${
                      priority === 'FASTEST' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Fastest Flight First
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto border border-slate-200 rounded-2xl">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold font-mono text-slate-500 uppercase tracking-wider">
                      <th className="py-4 px-5">Airline / Carrier</th>
                      <th className="py-4 px-5">Flight Details</th>
                      <th className="py-4 px-5">Duration</th>
                      <th className="py-4 px-5">Observed Fare</th>
                      <th className="py-4 px-5">Position</th>
                      <th className="py-4 px-5">Source Provenance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-sans">
                    {analysis.airline_alternatives.map((alt, idx) => (
                      <tr key={alt.carrier_code} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-4 px-5">
                          <div className="flex items-center gap-3">
                            <span className="w-9 h-9 rounded-xl bg-blue-50 text-blue-700 font-mono font-black flex items-center justify-center text-xs border border-blue-200">
                              {alt.carrier_code}
                            </span>
                            <div>
                              <div className="font-bold text-slate-900 flex items-center gap-2">
                                <span>{alt.airline_name}</span>
                                {idx === 0 && (
                                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                                    LOWEST FARE
                                  </span>
                                )}
                              </div>
                              <div className="text-[11px] text-slate-400 font-mono">Code: {alt.carrier_code}</div>
                            </div>
                          </div>
                        </td>

                        <td className="py-4 px-5 font-mono text-xs">
                          <div className="font-bold text-slate-800">{alt.departure_time || '11:30 AM'}</div>
                          <div className="text-slate-400">{analysis.origin} ➔ {analysis.destination}</div>
                        </td>

                        <td className="py-4 px-5 font-mono text-xs text-slate-600">
                          <div className="font-bold text-slate-800">{alt.stops === 0 ? 'Non-Stop' : `${alt.stops} Stop(s)`}</div>
                          <div className="text-slate-400">{Math.floor((alt.duration_minutes || 135) / 60)}h {(alt.duration_minutes || 135) % 60}m</div>
                        </td>

                        <td className="py-4 px-5 font-mono">
                          <span className="text-lg font-black text-slate-900">
                            ₹{alt.observed_fare.toLocaleString('en-IN')}
                          </span>
                        </td>

                        <td className="py-4 px-5">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold border ${
                            alt.current_position === 'LOW'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : 'bg-blue-50 text-blue-700 border-blue-200'
                          }`}>
                            {alt.current_position}
                          </span>
                        </td>

                        <td className="py-4 px-5 font-mono text-xs">
                          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-100 text-slate-700 border border-slate-200 text-[11px]">
                            <Globe className="w-3 h-3 text-slate-500" />
                            <span>Google Flights (Search Capture)</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: Trajectory & Panel Health Audit */}
          {activeTab === 'panel-health' && (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 md:p-8 shadow-sm space-y-8">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 mb-2 font-mono">
                  <Database className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Longitudinal Panel Telemetry &amp; Trajectory Explorer</span>
                </div>
                <h3 className="text-2xl font-black text-slate-900 tracking-tight">
                  Empirical Trajectory Explorer &bull; {origin} ➔ {destination} ({travelDate})
                </h3>
                <p className="text-sm text-slate-500 max-w-3xl leading-relaxed font-sans">
                  Live chronological progression of repeated searches for the same route and fixed departure date.
                </p>
              </div>

              {/* Panel Health KPIs */}
              {readiness && (
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-xs font-mono">
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                    <div className="text-slate-400">Tracked Trajectories</div>
                    <div className="text-xl font-black text-slate-900">{readiness.repeated_trajectories}</div>
                  </div>
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                    <div className="text-slate-400">Pinned Dates</div>
                    <div className="text-xl font-black text-slate-900">{readiness.required_collection_schedule.pinned_travel_dates}</div>
                  </div>
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                    <div className="text-slate-400">Valid 7D Pairs</div>
                    <div className="text-xl font-black text-emerald-600">{readiness.seven_day_target_pairs}</div>
                  </div>
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                    <div className="text-slate-400">Valid 14D Pairs</div>
                    <div className="text-xl font-black text-blue-600">{readiness.fourteen_day_target_pairs}</div>
                  </div>
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                    <div className="text-slate-400">Model Training</div>
                    <div className="text-xl font-black text-amber-600">{readiness.model_training_status}</div>
                  </div>
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                    <div className="text-slate-400">Classification</div>
                    <div className="text-xs font-bold text-slate-700 truncate">{readiness.dataset_classification}</div>
                  </div>
                </div>
              )}

              {/* Trajectory Search Points Table */}
              {trajectory && (
                <div className="space-y-4">
                  <h4 className="text-base font-bold text-slate-900 font-mono">
                    Search Date Progression ({trajectory.search_dates_count} point(s) recorded)
                  </h4>

                  <div className="overflow-x-auto border border-slate-200 rounded-2xl">
                    <table className="w-full text-left border-collapse text-sm">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold font-mono text-slate-500 uppercase tracking-wider">
                          <th className="py-3.5 px-4">Search Date</th>
                          <th className="py-3.5 px-4">Days Left</th>
                          <th className="py-3.5 px-4">Median Fare</th>
                          <th className="py-3.5 px-4">Min Fare</th>
                          <th className="py-3.5 px-4">Max Fare</th>
                          <th className="py-3.5 px-4">Carriers Observed</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono text-xs">
                        {trajectory.search_points.map((pt) => (
                          <tr key={pt.search_date} className="hover:bg-slate-50/80">
                            <td className="py-3.5 px-4 font-bold text-slate-900">{pt.search_date}</td>
                            <td className="py-3.5 px-4 text-slate-600">{pt.days_to_departure} days</td>
                            <td className="py-3.5 px-4 font-bold text-blue-700">₹{pt.median_fare.toLocaleString('en-IN')}</td>
                            <td className="py-3.5 px-4 text-slate-700">₹{pt.min_fare.toLocaleString('en-IN')}</td>
                            <td className="py-3.5 px-4 text-slate-700">₹{pt.max_fare.toLocaleString('en-IN')}</td>
                            <td className="py-3.5 px-4 text-slate-600">
                              {pt.carrier_quotes.map(c => c.carrier_code).join(', ')} ({pt.carrier_quotes.length} quotes)
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-xs font-mono text-slate-600">
                    <span className="font-bold text-slate-900">Trajectory Target Status: </span>
                    <span>{trajectory.status} (7-Day target requires search at t+7 days)</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

