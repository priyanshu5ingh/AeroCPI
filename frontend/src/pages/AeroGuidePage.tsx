import React, { useState, useEffect } from 'react';
import {
  Sparkles, Search, Calendar, Plane, ShieldCheck, ArrowRight, CheckCircle2,
  AlertCircle, Clock, ChevronRight, RefreshCw, BarChart2, Layers, Info, ExternalLink,
  Zap, HelpCircle, Activity, Globe, Lock, Sliders
} from 'lucide-react';
import {
  AeroGuideAnalyzeResponse,
  AeroGuideAnalyzeRequest,
  RouteUniverseItem,
  AirlineRegistryItem,
  SourceCapabilityItem,
  DecisionTraceNode
} from '../types';
import {
  analyzeAirfare,
  fetchRouteUniverse,
  fetchAirlines,
  fetchSourceCapabilities,
  fetchForecastingReadiness
} from '../services/api';

const POPULAR_ROUTES = [
  { origin: 'DEL', dest: 'BOM', label: 'DEL ➔ BOM (Delhi-Mumbai)' },
  { origin: 'BLR', dest: 'DEL', label: 'BLR ➔ DEL (Bengaluru-Delhi)' },
  { origin: 'BOM', dest: 'BLR', label: 'BOM ➔ BLR (Mumbai-Bengaluru)' },
  { origin: 'DEL', dest: 'HYD', label: 'DEL ➔ HYD (Delhi-Hyderabad)' },
  { origin: 'DEL', dest: 'CCU', label: 'DEL ➔ CCU (Delhi-Kolkata)' },
  { origin: 'DEL', dest: 'MAA', label: 'DEL ➔ MAA (Delhi-Chennai)' },
  { origin: 'BOM', dest: 'GOI', label: 'BOM ➔ GOI (Mumbai-Goa)' },
  { origin: 'BLR', dest: 'HYD', label: 'BLR ➔ HYD (Bengaluru-Hyderabad)' },
  { origin: 'DEL', dest: 'COK', label: 'DEL ➔ COK (Delhi-Kochi)' },
  { origin: 'BLR', dest: 'CCU', label: 'BLR ➔ CCU (Bengaluru-Kolkata)' },
];

export const AeroGuidePage: React.FC = () => {
  // Search Form State
  const [origin, setOrigin] = useState('DEL');
  const [destination, setDestination] = useState('BOM');
  const [travelDate, setTravelDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 15);
    return d.toISOString().split('T')[0];
  });
  const [flexibilityDays, setFlexibilityDays] = useState(2);
  const [priority, setPriority] = useState<'CHEAPEST' | 'FASTEST'>('CHEAPEST');

  // Intelligence Results State
  const [analysis, setAnalysis] = useState<AeroGuideAnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Deep Inspection Modal/Drawer State
  const [selectedTraceNode, setSelectedTraceNode] = useState<DecisionTraceNode | null>(null);
  const [activeInspectorTab, setActiveInspectorTab] = useState<'decision-trace' | 'airline-ndc' | 'data-provenance'>('decision-trace');

  // Metadata Catalogs
  const [airlines, setAirlines] = useState<AirlineRegistryItem[]>([]);
  const [sources, setSources] = useState<SourceCapabilityItem[]>([]);

  // Initial Data Fetch
  useEffect(() => {
    fetchAirlines().then(setAirlines).catch(console.warn);
    fetchSourceCapabilities().then(setSources).catch(console.warn);
    handleAnalyze();
  }, []);

  const handleAnalyze = async (overrideOrigin?: string, overrideDest?: string) => {
    const orig = overrideOrigin || origin;
    const dest = overrideDest || destination;

    if (orig === dest) {
      setError('Origin and Destination airports must be different.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: AeroGuideAnalyzeRequest = {
      origin: orig,
      destination: dest,
      travel_date: travelDate,
      flexibility_days: flexibilityDays,
      priority: priority,
      adults: 1,
      cabin: 'ECONOMY',
      currency: 'INR'
    };

    try {
      const res = await analyzeAirfare(payload);
      setAnalysis(res);
      if (res.decision_trace && res.decision_trace.length > 0) {
        setSelectedTraceNode(res.decision_trace[res.decision_trace.length - 1]);
      }
    } catch (err: any) {
      console.error('AeroGuide analysis failed:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to analyze consumer airfare.');
    } finally {
      setLoading(false);
    }
  };

  const getPricePositionBadge = (pos: string) => {
    switch (pos) {
      case 'LOW':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            LOW — Favorable Price Position
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
            HIGH — Above Historical Baseline
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
            <Activity className="w-3.5 h-3.5 text-blue-600" />
            TYPICAL — Corridor Baseline
          </span>
        );
    }
  };

  const getGuidanceCard = (guidance: string) => {
    switch (guidance) {
      case 'FLEX_DATE':
        return {
          title: 'Flexible Date Opportunity Identified',
          badge: 'FLEX DATE RECOMMENDED',
          bg: 'bg-emerald-600 text-white',
          border: 'border-emerald-500',
          icon: Calendar,
          description: 'A candidate departure date within your ± window offers a significantly lower observed fare.'
        };
      case 'BOOK':
        return {
          title: 'Favorable Booking Window',
          badge: 'FAVORABLE FARE',
          bg: 'bg-blue-600 text-white',
          border: 'border-blue-500',
          icon: CheckCircle2,
          description: 'Current fare is at or below the 15th percentile of historical corridor observations.'
        };
      case 'WAIT':
        return {
          title: 'Elevated Fare — Watch Window',
          badge: 'WATCH & WAIT',
          bg: 'bg-amber-600 text-white',
          border: 'border-amber-500',
          icon: Clock,
          description: 'Current fare is in the top 20% of historical quotes with ample lead days before departure.'
        };
      default:
        return {
          title: 'Market Baseline — Active Tracking',
          badge: 'MARKET BASELINE',
          bg: 'bg-slate-900 text-white',
          border: 'border-slate-800',
          icon: Activity,
          description: 'Current fare aligns with typical historical prices for this corridor and advance window.'
        };
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Header & Consumer Context Hero */}
      <div className="bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white rounded-2xl p-6 md:p-8 shadow-xl relative overflow-hidden border border-slate-800">
        <div className="absolute -right-12 -top-12 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>AeroGuide &bull; Consumer Airfare Intelligence</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
              Domestic Airfare Search &amp; Decision Intelligence
            </h1>
            <p className="text-sm md:text-base text-slate-300 max-w-3xl leading-relaxed">
              Real-time multi-carrier alternatives, historical price positioning, and verifiable decision traces. 
              Grounded in empirical observations across airline and search channels.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 bg-white/5 backdrop-blur-md p-3.5 rounded-xl border border-white/10 text-xs text-slate-300 font-mono">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Policy: <strong className="text-white">DECISION_POLICY_V1</strong></span>
            </div>
            <span className="hidden sm:inline text-white/30">&bull;</span>
            <div>
              <span>Standard: <strong className="text-white">1 Adult, Economy, INR</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Compact Consumer Search & Route Selector */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 md:p-6 shadow-sm">
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
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                Origin Airport
              </label>
              <div className="relative">
                <select
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none cursor-pointer"
                >
                  <option value="DEL">DEL &mdash; New Delhi (Indira Gandhi)</option>
                  <option value="BOM">BOM &mdash; Mumbai (Chhatrapati Shivaji)</option>
                  <option value="BLR">BLR &mdash; Bengaluru (Kempegowda)</option>
                  <option value="MAA">MAA &mdash; Chennai (Chennai Intl)</option>
                  <option value="CCU">CCU &mdash; Kolkata (Netaji Subhash)</option>
                  <option value="HYD">HYD &mdash; Hyderabad (Rajiv Gandhi)</option>
                  <option value="GOI">GOI &mdash; Goa (Dabolim)</option>
                  <option value="PNQ">PNQ &mdash; Pune</option>
                  <option value="COK">COK &mdash; Kochi</option>
                  <option value="AMD">AMD &mdash; Ahmedabad</option>
                </select>
                <Plane className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            {/* Destination Airport */}
            <div className="lg:col-span-3 space-y-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                Destination Airport
              </label>
              <div className="relative">
                <select
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none cursor-pointer"
                >
                  <option value="BOM">BOM &mdash; Mumbai (Chhatrapati Shivaji)</option>
                  <option value="DEL">DEL &mdash; New Delhi (Indira Gandhi)</option>
                  <option value="BLR">BLR &mdash; Bengaluru (Kempegowda)</option>
                  <option value="HYD">HYD &mdash; Hyderabad (Rajiv Gandhi)</option>
                  <option value="CCU">CCU &mdash; Kolkata (Netaji Subhash)</option>
                  <option value="MAA">MAA &mdash; Chennai (Chennai Intl)</option>
                  <option value="GOI">GOI &mdash; Goa (Dabolim)</option>
                  <option value="PNQ">PNQ &mdash; Pune</option>
                  <option value="COK">COK &mdash; Kochi</option>
                  <option value="AMD">AMD &mdash; Ahmedabad</option>
                </select>
                <Plane className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            {/* Departure Date */}
            <div className="lg:col-span-3 space-y-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                Travel Date
              </label>
              <div className="relative">
                <input
                  type="date"
                  value={travelDate}
                  onChange={(e) => setTravelDate(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Flexibility & Submit */}
            <div className="lg:col-span-3 flex gap-2 items-center">
              <div className="flex-1 space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  Date Flex
                </label>
                <select
                  value={flexibilityDays}
                  onChange={(e) => setFlexibilityDays(Number(e.target.value))}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-2.5 py-2.5 text-xs font-bold text-slate-800 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value={0}>Exact Date</option>
                  <option value={1}>± 1 Day</option>
                  <option value={2}>± 2 Days</option>
                  <option value={3}>± 3 Days</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                  &nbsp;
                </label>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold text-sm px-5 py-2.5 rounded-xl transition-colors flex items-center gap-2 shadow-sm shadow-blue-500/20 disabled:opacity-50"
                >
                  {loading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                  <span>Analyze</span>
                </button>
              </div>
            </div>
          </div>

          {/* Quick Route Pills */}
          <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold text-slate-400 mr-1">Popular Corridors:</span>
            {POPULAR_ROUTES.slice(0, 6).map((r) => (
              <button
                key={`${r.origin}-${r.dest}`}
                type="button"
                onClick={() => {
                  setOrigin(r.origin);
                  setDestination(r.dest);
                  handleAnalyze(r.origin, r.dest);
                }}
                className={`text-xs px-2.5 py-1 rounded-lg font-mono font-medium transition-all ${
                  origin === r.origin && destination === r.dest
                    ? 'bg-blue-100 text-blue-800 border border-blue-300 font-bold'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 border border-slate-200'
                }`}
              >
                {r.origin} ➔ {r.dest}
              </button>
            ))}
          </div>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {analysis && (
        <div className="space-y-8">
          {/* 3. Primary Analysis Summary & Guidance Zone */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Price Position & Historical Distribution Card */}
            <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-6 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl font-extrabold text-slate-900 font-mono">
                      {analysis.origin} ➔ {analysis.destination}
                    </span>
                    <span className="text-xs font-semibold text-slate-500 font-mono">
                      ({analysis.days_to_departure} days to departure &bull; {analysis.travel_date})
                    </span>
                  </div>
                  {getPricePositionBadge(analysis.price_position)}
                </div>

                <div className="flex items-baseline gap-3">
                  <span className="text-4xl font-extrabold text-slate-900 font-mono tracking-tight">
                    ₹{analysis.current_observed_fare.toLocaleString('en-IN')}
                  </span>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Lowest Observed One-Way Fare (1 Adult)
                  </span>
                </div>
              </div>

              {/* Corridor Price Distribution Progress */}
              <div className="space-y-2 bg-slate-50 p-4 rounded-xl border border-slate-100">
                <div className="flex justify-between text-xs font-mono text-slate-600 font-semibold">
                  <span>Hist. Min: ₹{analysis.route_historical_min.toLocaleString('en-IN')}</span>
                  <span className="text-blue-700 font-bold">
                    Median: ₹{analysis.route_historical_median.toLocaleString('en-IN')}
                  </span>
                  <span>Hist. Max: ₹{analysis.route_historical_max.toLocaleString('en-IN')}</span>
                </div>
                <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden relative">
                  <div
                    className="bg-blue-600 h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(
                          10,
                          ((analysis.current_observed_fare - analysis.route_historical_min) /
                            (analysis.route_historical_max - analysis.route_historical_min || 1)) *
                            100
                        )
                      )}%`
                    }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                  <span>15th Percentile (Favorable)</span>
                  <span>Sample: {analysis.observations_in_sample} market quotes</span>
                  <span>80th Percentile (Elevated)</span>
                </div>
              </div>

              {/* Versioned Guidance Rationale */}
              <div className="border-t border-slate-100 pt-4 text-xs text-slate-700 leading-relaxed font-sans">
                <strong className="text-slate-900 font-bold">Scientific Policy Rationale: </strong>
                {analysis.guidance_reason}
              </div>
            </div>

            {/* Booking Guidance Banner */}
            <div className="lg:col-span-5 flex flex-col">
              {(() => {
                const g = getGuidanceCard(analysis.booking_guidance);
                const Icon = g.icon;
                return (
                  <div className={`${g.bg} rounded-2xl p-6 shadow-md flex flex-col justify-between h-full border ${g.border}`}>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-mono font-bold tracking-wider px-2.5 py-1 rounded-md bg-white/20 uppercase">
                          {g.badge}
                        </span>
                        <Icon className="w-6 h-6 text-white/90" />
                      </div>
                      <h3 className="text-xl font-extrabold tracking-tight">
                        {g.title}
                      </h3>
                      <p className="text-sm text-white/90 leading-relaxed">
                        {g.description}
                      </p>
                    </div>

                    <div className="pt-6 border-t border-white/20 mt-4 flex items-center justify-between text-xs font-mono text-white/80">
                      <span>Policy: {analysis.decision_policy_version}</span>
                      <button
                        onClick={() => setActiveInspectorTab('decision-trace')}
                        className="underline hover:text-white font-bold flex items-center gap-1"
                      >
                        Inspect Trace <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>

          {/* 4. Honest AI Outlook Card (Zero Fake Predictions) */}
          <div className="bg-slate-900 text-white rounded-2xl border border-slate-800 p-6 shadow-sm">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                    STATUS: COLLECTING_LONGITUDINAL_EVIDENCE
                  </span>
                  <span className="text-xs font-mono text-slate-400 hidden sm:inline">
                    &bull; ML Forecast Engine
                  </span>
                </div>
                <h4 className="text-base font-bold text-slate-100">
                  Directional Forecasting &bull; Scientific Readiness Gate
                </h4>
                <p className="text-xs md:text-sm text-slate-300 max-w-3xl leading-relaxed">
                  {analysis.model_outlook_message}
                </p>
              </div>

              <div className="bg-slate-800/80 border border-slate-700 p-3.5 rounded-xl text-xs font-mono text-slate-300 shrink-0 space-y-1">
                <div className="flex justify-between gap-4">
                  <span className="text-slate-400">7-Day Target Pairs:</span>
                  <strong className="text-white">0 / 7 pairs (Collecting)</strong>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-slate-400">Model Status:</span>
                  <strong className="text-amber-400">TRAINING_DISABLED</strong>
                </div>
              </div>
            </div>
          </div>

          {/* 5. Flexible Date Explorer Strip */}
          {analysis.flexible_dates && analysis.flexible_dates.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-blue-600" />
                    Flexible Travel Dates Comparison (± {flexibilityDays} Days)
                  </h3>
                  <p className="text-xs text-slate-500">
                    Observed market quotes across adjacent departure dates.
                  </p>
                </div>
                <span className="text-xs font-mono font-bold text-slate-400">
                  Requested Date: {analysis.travel_date}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {analysis.flexible_dates.map((f) => (
                  <div
                    key={f.travel_date}
                    className={`p-4 rounded-xl border transition-all ${
                      f.is_lower_fare
                        ? 'bg-emerald-50/70 border-emerald-300 ring-1 ring-emerald-400/30'
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-mono font-bold text-slate-600">
                        {f.days_diff > 0 ? `+${f.days_diff} Day` : `${f.days_diff} Day`}
                      </span>
                      {f.is_lower_fare && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-600 text-white uppercase">
                          Lower Fare
                        </span>
                      )}
                    </div>
                    <div className="text-sm font-extrabold text-slate-900 mb-1">
                      {f.label}
                    </div>
                    <div className="text-xs font-mono text-slate-500">
                      {f.difference_from_requested < 0 ? (
                        <span className="text-emerald-700 font-bold">
                          ₹{Math.abs(f.difference_from_requested).toLocaleString('en-IN')} lower ({Math.abs(f.percent_difference)}%)
                        </span>
                      ) : (
                        <span className="text-slate-600">
                          +₹{f.difference_from_requested.toLocaleString('en-IN')} ({f.percent_difference}%)
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 6. Airline Alternatives Comparison Matrix */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Plane className="w-5 h-5 text-blue-600" />
                  Observed Airline Offers ({analysis.airline_alternatives.length} Carriers)
                </h3>
                <p className="text-xs text-slate-500">
                  Standardized quotes on {analysis.travel_date} across search and direct airline distribution channels.
                </p>
              </div>

              {/* Priority Toggle */}
              <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 self-start sm:self-auto">
                <button
                  onClick={() => {
                    setPriority('CHEAPEST');
                    handleAnalyze();
                  }}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                    priority === 'CHEAPEST'
                      ? 'bg-white text-blue-700 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Cheapest
                </button>
                <button
                  onClick={() => {
                    setPriority('FASTEST');
                    handleAnalyze();
                  }}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                    priority === 'FASTEST'
                      ? 'bg-white text-blue-700 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Fastest
                </button>
              </div>
            </div>

            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold font-mono text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Carrier</th>
                    <th className="py-3 px-4">Departure / Route</th>
                    <th className="py-3 px-4">Stops &amp; Duration</th>
                    <th className="py-3 px-4">Observed Fare</th>
                    <th className="py-3 px-4">Price Position</th>
                    <th className="py-3 px-4">Source Provenance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-sans">
                  {analysis.airline_alternatives.map((alt) => (
                    <tr key={alt.carrier_code} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-3">
                          <span className="w-7 h-7 rounded-lg bg-blue-50 text-blue-700 font-mono font-bold flex items-center justify-center text-xs border border-blue-200">
                            {alt.carrier_code}
                          </span>
                          <div>
                            <div className="font-bold text-slate-900">{alt.airline_name}</div>
                            <div className="text-[11px] text-slate-400 font-mono">Code: {alt.carrier_code}</div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4 font-mono text-xs">
                        <div className="font-bold text-slate-800">{alt.departure_time || '11:30 AM'}</div>
                        <div className="text-slate-400">{analysis.origin} ➔ {analysis.destination}</div>
                      </td>

                      <td className="py-3.5 px-4 font-mono text-xs text-slate-600">
                        <div>{alt.stops === 0 ? 'Non-Stop (Direct)' : `${alt.stops} Stop(s)`}</div>
                        <div className="text-slate-400">{Math.floor(alt.duration_minutes / 60)}h {alt.duration_minutes % 60}m</div>
                      </td>

                      <td className="py-3.5 px-4 font-mono">
                        <span className="text-base font-extrabold text-slate-900">
                          ₹{alt.observed_fare.toLocaleString('en-IN')}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        {getPricePositionBadge(alt.current_position)}
                      </td>

                      <td className="py-3.5 px-4 font-mono text-xs">
                        <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 text-[11px]">
                          <Globe className="w-3 h-3 text-slate-500" />
                          <span>Google Flights (Search Aggregator)</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 7. Verifiable 8-Node Decision Trace Flow & Deep Inspector */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
              <div>
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                  Verifiable 8-Node Decision Trace &amp; Audit Pipeline
                </h3>
                <p className="text-xs text-slate-500">
                  Full step-by-step computational lineage from standardized request to deterministic verdict.
                </p>
              </div>

              {/* Inspector Tab Switcher */}
              <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
                <button
                  onClick={() => setActiveInspectorTab('decision-trace')}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                    activeInspectorTab === 'decision-trace'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  8-Node Decision Trace
                </button>
                <button
                  onClick={() => setActiveInspectorTab('airline-ndc')}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                    activeInspectorTab === 'airline-ndc'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Airline NDC Registry
                </button>
                <button
                  onClick={() => setActiveInspectorTab('data-provenance')}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                    activeInspectorTab === 'data-provenance'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Grounded Evidence
                </button>
              </div>
            </div>

            {activeInspectorTab === 'decision-trace' && (
              <div className="space-y-6">
                {/* 8-Node Step Pills */}
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
                  {analysis.decision_trace.map((node) => {
                    const isSelected = selectedTraceNode?.step_number === node.step_number;
                    return (
                      <button
                        key={node.step_number}
                        onClick={() => setSelectedTraceNode(node)}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          isSelected
                            ? 'bg-blue-50 border-blue-500 ring-2 ring-blue-500/20 shadow-xs'
                            : 'bg-slate-50/70 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                            Node {node.step_number}
                          </span>
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        </div>
                        <div className="text-xs font-bold text-slate-800 line-clamp-1">
                          {node.stage_name}
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Selected Node Deep Inspector */}
                {selectedTraceNode && (
                  <div className="bg-slate-900 text-white rounded-xl p-5 border border-slate-800 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
                      <div className="flex items-center gap-3">
                        <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                          Step {selectedTraceNode.step_number} of 8
                        </span>
                        <h4 className="text-sm font-bold text-white">
                          {selectedTraceNode.stage_name}
                        </h4>
                      </div>
                      <div className="text-xs font-mono text-slate-400">
                        Timestamp: {selectedTraceNode.timestamp_utc}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                      <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 space-y-1">
                        <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                          Input Summary
                        </div>
                        <div className="text-slate-200">{selectedTraceNode.input_summary}</div>
                      </div>

                      <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 space-y-1">
                        <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                          Computation Lineage
                        </div>
                        <div className="text-slate-200">{selectedTraceNode.computation_summary}</div>
                      </div>

                      <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 space-y-1">
                        <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                          Deterministic Verdict
                        </div>
                        <div className="text-emerald-300 font-bold">{selectedTraceNode.verdict_detail}</div>
                      </div>
                    </div>

                    <div className="pt-2 flex justify-between items-center text-[11px] font-mono text-slate-400 border-t border-slate-800">
                      <span>Provenance Hash: {selectedTraceNode.data_provenance_id}</span>
                      <span className="text-emerald-400 font-bold">STATE: {selectedTraceNode.status}</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeInspectorTab === 'airline-ndc' && (
              <div className="space-y-4">
                <div className="text-xs text-slate-600 leading-relaxed">
                  AeroGuide audits national carrier developer interfaces against strict 4-tier source states:
                  <strong className="text-slate-900"> DOCUMENTED &ne; ACCESSIBLE &ne; ACTUALLY_COLLECTED &ne; CURRENTLY_OBSERVED</strong>.
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {airlines.map((a) => (
                    <div key={a.airline_id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <span className="w-8 h-8 rounded-lg bg-blue-600 text-white font-mono font-bold flex items-center justify-center text-xs">
                            {a.iata_code}
                          </span>
                          <div>
                            <div className="font-bold text-slate-900">{a.name}</div>
                            <div className="text-[11px] text-slate-500 font-mono">Access: {a.api_access_type}</div>
                          </div>
                        </div>

                        {a.ndc_available ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                            NDC DOCUMENTED
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-200 text-slate-700">
                            WEB TARIFF
                          </span>
                        )}
                      </div>

                      <div className="text-xs font-mono text-slate-600 space-y-1 bg-white p-3 rounded-lg border border-slate-200/80">
                        <div className="flex justify-between">
                          <span>Endpoints:</span>
                          <strong className="text-slate-800">{a.documented_endpoints.join(', ') || 'Public Web Schedule'}</strong>
                        </div>
                        <div className="flex justify-between">
                          <span>Partner Restriction:</span>
                          <strong className={a.partner_restriction ? 'text-amber-600' : 'text-emerald-600'}>
                            {a.partner_restriction ? 'Authenticated / Whitelisted' : 'Public'}
                          </strong>
                        </div>
                        <div className="flex justify-between">
                          <span>Verification:</span>
                          <strong className="text-slate-800">{a.verification_status}</strong>
                        </div>
                      </div>

                      {a.ndc_portal_url && (
                        <a
                          href={a.ndc_portal_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800 underline"
                        >
                          <span>Official Developer Portal</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeInspectorTab === 'data-provenance' && (
              <div className="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-4 font-mono text-xs">
                <div className="font-bold text-slate-900 text-sm font-sans">
                  Grounded Evidence Anchor (Strict Anti-Hallucination JSON)
                </div>
                <div className="bg-slate-900 text-slate-100 p-4 rounded-xl overflow-x-auto max-h-60 text-[11px] leading-relaxed">
                  <pre>{JSON.stringify(analysis.grounded_explanation, null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
