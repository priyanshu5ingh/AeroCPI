import React, { useState, useEffect, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { drawerVariants, drawerBackdropVariants } from '../lib/motion';
import {
  Search,
  Filter,
  ArrowRight,
  Clock,
  Compass,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  X,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  Database,
  Layers,
  Activity,
  FileText,
  RefreshCw,
  SlidersHorizontal,
  Plane,
  Eye,
  Calendar,
  DollarSign,
  AlertTriangle
} from 'lucide-react';
import { IndexDashboardResponse, ObservationExplorerItem, ObservationExplorerResponse } from '../types';
import { fetchObservationExplorer } from '../services/api';

interface LiveMarketPageProps {
  dashboard: IndexDashboardResponse;
  onSelectRoute?: (routeId: string) => void;
}

const BASKET_ROUTES = [
  'DEL-BOM',
  'BLR-DEL',
  'BLR-BOM',
  'DEL-HYD',
  'DEL-CCU',
  'MAA-DEL',
  'GOI-BOM',
  'BLR-HYD',
  'DEL-PAT',
  'BLR-CCU',
];

const HORIZONS = [
  { value: '1', label: 'T+1 (1 Day Ahead)' },
  { value: '7', label: 'T+7 (1 Week Ahead)' },
  { value: '15', label: 'T+15 (AeroCPI Headline)' },
  { value: '30', label: 'T+30 (1 Month Ahead)' },
  { value: '45', label: 'T+45 (6 Weeks Ahead)' },
];

const CARRIER_MAP: Record<string, string> = {
  '6E': 'IndiGo (6E)',
  'AI': 'Air India (AI)',
  'QP': 'Akasa Air (QP)',
  'SG': 'SpiceJet (SG)',
  'S5': 'Star Air (S5)',
  'UNKNOWN': 'Carrier Unspecified',
};

export const LiveMarketPage: React.FC<LiveMarketPageProps> = ({ dashboard, onSelectRoute }) => {
  const scope = dashboard.dashboard_scope;
  const audit = dashboard.audit;

  // Filter States
  const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();
  const [selectedRoute, setSelectedRoute] = useState<string>(searchParams.get('route') || '');
  const [selectedHorizon, setSelectedHorizon] = useState<string>(searchParams.get('horizon') || '');
  const [selectedCarrier, setSelectedCarrier] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedValidation, setSelectedValidation] = useState<string>('');
  const [selectedEligibility, setSelectedEligibility] = useState<string>('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    let changed = false;
    
    if (selectedRoute) { params.set('route', selectedRoute); changed = true; }
    else if (params.has('route')) { params.delete('route'); changed = true; }
    
    if (selectedHorizon) { params.set('horizon', selectedHorizon); changed = true; }
    else if (params.has('horizon')) { params.delete('horizon'); changed = true; }
    
    if (changed) {
      window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`);
    }
  }, [selectedRoute, selectedHorizon]);

  // Pagination States
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(50);

  // Data States
  const [data, setData] = useState<ObservationExplorerResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Evidence Drawer State
  const [selectedObs, setSelectedObs] = useState<ObservationExplorerItem | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Fetch observations whenever filters or page change
  const loadObservations = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchObservationExplorer({
        route_id: selectedRoute || undefined,
        horizon: selectedHorizon ? parseInt(selectedHorizon, 10) : undefined,
        carrier: selectedCarrier || undefined,
        collection_date: selectedDate || undefined,
        validation_status: selectedValidation || undefined,
        index_eligibility: selectedEligibility || undefined,
        page,
        page_size: pageSize,
      });
      setData(res);
    } catch (err: any) {
      console.error('Failed to load observation explorer records:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch observations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadObservations();
  }, [selectedRoute, selectedHorizon, selectedCarrier, selectedDate, selectedValidation, selectedEligibility, page, pageSize]);

  // Reset page to 1 when filters change
  const handleFilterChange = (setter: React.Dispatch<React.SetStateAction<string>>, value: string) => {
    setter(value);
    setPage(1);
  };

  const handleResetFilters = () => {
    setSelectedRoute('');
    setSelectedHorizon('');
    setSelectedCarrier('');
    setSelectedDate('');
    setSelectedValidation('');
    setSelectedEligibility('');
    setPage(1);
  };

  const hasActiveFilters = Boolean(
    selectedRoute || selectedHorizon || selectedCarrier || selectedDate || selectedValidation || selectedEligibility
  );

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(text);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Compact fare distribution visual (purely displays min/max of returned page items without client-side stats)
  const fareSpread = useMemo(() => {
    if (!data || data.observations.length === 0) return null;
    let min = data.observations[0].total_fare;
    let max = data.observations[0].total_fare;
    for (const o of data.observations) {
      if (o.total_fare < min) min = o.total_fare;
      if (o.total_fare > max) max = o.total_fare;
    }
    return { min, max };
  }, [data]);

  return (
    <div className="space-y-6">
      {/* 1. Header & Telemetry Ledger Strip */}
      <div className="surface-solid p-6 sm:p-7 relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200/80">
                <Search className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                    OBSERVATION EXPLORER
                  </h1>
                  <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200/80 uppercase">
                    Evidence Ledger
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Inspect and audit raw commercial flight quotes supporting the AeroCPI sovereign basket.
                </p>
              </div>
            </div>
          </div>

          {/* Telemetry Counter Chips */}
          <div className="flex items-center gap-3 flex-wrap text-xs">
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-1.5 font-mono text-slate-700 shadow-xs">
              <span className="text-slate-400 mr-1.5">POPULATION:</span>
              <span className="font-bold text-blue-600 mono-number">
                {data ? data.total.toLocaleString() : '5,332'}
              </span>
              <span className="text-slate-400 ml-1">quotes</span>
            </div>

            <div className="bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-1.5 font-mono text-slate-700 shadow-xs">
              <span className="text-slate-400 mr-1.5">CORRIDORS:</span>
              <span className="font-bold text-slate-900">10 DGCA Sovereign</span>
            </div>

            <div className="bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-1.5 font-mono text-slate-700 shadow-xs">
              <span className="text-slate-400 mr-1.5">HORIZONS:</span>
              <span className="font-bold text-slate-900">5 (T+1 to T+45)</span>
            </div>

            <div className="bg-emerald-50 text-emerald-700 border border-emerald-200/90 rounded-xl px-3 py-1.5 font-mono text-[11px] font-bold shadow-xs flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>SERVER-CERTIFIED</span>
            </div>
          </div>
        </div>

        {/* Dynamic Multi-Dimensional Filter Bar */}
        <div className="pt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          {/* Corridor Filter */}
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Corridor
            </label>
            <select
              value={selectedRoute}
              onChange={(e) => handleFilterChange(setSelectedRoute, e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-2.5 py-1.5 text-xs font-mono font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="">All Corridors (10)</option>
              {BASKET_ROUTES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          {/* Horizon Filter */}
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Advance Horizon
            </label>
            <select
              value={selectedHorizon}
              onChange={(e) => handleFilterChange(setSelectedHorizon, e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-2.5 py-1.5 text-xs font-mono font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="">All Horizons (5)</option>
              {HORIZONS.map((h) => (
                <option key={h.value} value={h.value}>
                  {h.label}
                </option>
              ))}
            </select>
          </div>

          {/* Dynamic Collection Date Filter */}
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Collection Window
            </label>
            <select
              value={selectedDate}
              onChange={(e) => handleFilterChange(setSelectedDate, e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-2.5 py-1.5 text-xs font-mono font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="">All Dates</option>
              <option value={scope.reference_date}>
                Ref: {scope.reference_date} (Baseline)
              </option>
              <option value={scope.calculation_date}>
                Calc: {scope.calculation_date} (Current)
              </option>
            </select>
          </div>

          {/* Airline Carrier Filter */}
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Airline Carrier
            </label>
            <select
              value={selectedCarrier}
              onChange={(e) => handleFilterChange(setSelectedCarrier, e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-2.5 py-1.5 text-xs font-mono font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="">All Carriers</option>
              {Object.entries(CARRIER_MAP).map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          {/* Validation Status */}
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Validation Status
            </label>
            <select
              value={selectedValidation}
              onChange={(e) => handleFilterChange(setSelectedValidation, e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-2.5 py-1.5 text-xs font-mono font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="">All Validation</option>
              <option value="FLAG">FLAG (Flagged Rules)</option>
              <option value="ACCEPT">ACCEPT (Rule Clean)</option>
            </select>
          </div>

          {/* Index Eligibility */}
          <div className="flex flex-col justify-between">
            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Index Eligibility
              </label>
              <select
                value={selectedEligibility}
                onChange={(e) => handleFilterChange(setSelectedEligibility, e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-2.5 py-1.5 text-xs font-mono font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                <option value="">All Eligibility</option>
                <option value="ELIGIBLE">ELIGIBLE</option>
                <option value="INELIGIBLE">INELIGIBLE</option>
              </select>
            </div>

            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="mt-2 text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 self-end cursor-pointer"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Reset Filters</span>
              </button>
            )}
          </div>
        </div>

        {/* Compact Fare Distribution Visual Strip (Visual Spread Only) */}
        {fareSpread && (
          <div className="mt-4 pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Page Fare Spread:</span>
              <span className="font-mono font-bold text-slate-800">
                ₹{fareSpread.min.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
              </span>
              <span className="text-slate-300">→</span>
              <span className="font-mono font-bold text-slate-800">
                ₹{fareSpread.max.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
              </span>
            </div>

            {/* Visual spectrum track representing raw returned bounds */}
            <div className="flex-1 max-w-xs h-2 bg-slate-100 rounded-full overflow-hidden relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400 via-indigo-500 to-blue-600 rounded-full opacity-80" />
            </div>

            <span className="text-[11px] text-slate-400 font-mono">
              N = {data?.observations.length || 0} quotes on this page
            </span>
          </div>
        )}
      </div>

      {/* 2. Main Observation Ledger Table & Slide-Over Drawer Container */}
      <div className="relative">
        <div className="surface-solid rounded-2xl overflow-hidden border border-slate-200/90 shadow-[0_2px_12px_-1px_rgba(15,23,42,0.03)]">
          {/* Table Header Bar */}
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                OBSERVATION LEDGER
              </h2>
            </div>

            <div className="flex items-center gap-3 text-xs">
              <span className="text-slate-500">
                Showing{' '}
                <span className="font-mono font-bold text-slate-900">
                  {data && data.total > 0 ? (page - 1) * pageSize + 1 : 0}
                </span>
                –
                <span className="font-mono font-bold text-slate-900">
                  {data ? Math.min(page * pageSize, data.total) : 0}
                </span>{' '}
                of{' '}
                <span className="font-mono font-bold text-slate-900">
                  {data ? data.total.toLocaleString() : 0}
                </span>
              </span>

              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(parseInt(e.target.value, 10));
                  setPage(1);
                }}
                className="bg-slate-50 border border-slate-200 text-slate-700 rounded-lg px-2 py-1 font-mono text-xs cursor-pointer focus:outline-none"
              >
                <option value={25}>25 / page</option>
                <option value={50}>50 / page</option>
                <option value={100}>100 / page</option>
              </select>
            </div>
          </div>

          {/* Table Content */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200/80 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">Observation ID</th>
                  <th className="py-3 px-4">Corridor</th>
                  <th className="py-3 px-4">Carrier</th>
                  <th className="py-3 px-4">Horizon</th>
                  <th className="py-3 px-4">Travel Date</th>
                  <th className="py-3 px-4 text-right">Total Fare (INR)</th>
                  <th className="py-3 px-4">Validation</th>
                  <th className="py-3 px-4">Eligibility</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {loading ? (
                  <tr>
                    <td colSpan={9} className="py-12 text-center text-slate-400">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
                        <span className="text-xs font-medium">Fetching observation records...</span>
                      </div>
                    </td>
                  </tr>
                ) : error ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-rose-600">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <AlertTriangle className="w-5 h-5" />
                        <span className="text-xs font-semibold">{error}</span>
                        <button
                          type="button"
                          onClick={loadObservations}
                          className="mt-1 px-3 py-1 rounded bg-rose-50 border border-rose-200 text-xs font-bold hover:bg-rose-100 cursor-pointer"
                        >
                          Retry Query
                        </button>
                      </div>
                    </td>
                  </tr>
                ) : data && data.observations.length > 0 ? (
                  data.observations.map((obs) => {
                    const isSelected = selectedObs?.observation_id === obs.observation_id;
                    return (
                      <tr
                        key={obs.observation_id}
                        onClick={() => setSelectedObs(obs)}
                        className={`hover:bg-slate-50/80 transition-colors cursor-pointer ${
                          isSelected ? 'bg-blue-50/50 ring-1 ring-blue-500/20' : ''
                        }`}
                      >
                        {/* Observation UUID */}
                        <td className="py-3 px-4 font-mono text-slate-600">
                          <span title={obs.observation_id}>
                            {obs.observation_id.substring(0, 8)}...
                          </span>
                        </td>

                        {/* Corridor */}
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5 font-mono font-bold text-slate-900">
                            <span>{obs.route_id}</span>
                          </div>
                        </td>

                        {/* Carrier */}
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md font-mono text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200/80">
                            {obs.carrier}
                          </span>
                        </td>

                        {/* Advance Horizon */}
                        <td className="py-3 px-4">
                          <span className="font-mono font-bold text-blue-700 bg-blue-50/80 px-2 py-0.5 rounded border border-blue-100 text-[11px]">
                            T+{obs.advance_purchase_days}
                          </span>
                        </td>

                        {/* Travel Date */}
                        <td className="py-3 px-4 font-mono text-slate-600">
                          {obs.travel_date || '—'}
                        </td>

                        {/* Fare (INR) */}
                        <td className="py-3 px-4 text-right">
                          <span className="font-mono font-bold text-slate-900 text-sm mono-number">
                            ₹{obs.total_fare.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </span>
                        </td>

                        {/* Validation Status (Exposed as-is from backend) */}
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                              obs.validation_status === 'ACCEPT'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : 'bg-amber-50 text-amber-700 border-amber-200'
                            }`}
                          >
                            {obs.validation_status}
                          </span>
                        </td>

                        {/* Index Eligibility (Exposed as-is from backend) */}
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                              obs.index_eligibility === 'ELIGIBLE'
                                ? 'bg-blue-50 text-blue-700 border-blue-200'
                                : 'bg-slate-100 text-slate-600 border-slate-200'
                            }`}
                          >
                            {obs.index_eligibility}
                          </span>
                        </td>

                        {/* Inspect Details Action */}
                        <td className="py-3 px-4 text-center">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedObs(obs);
                            }}
                            className="text-xs font-semibold text-blue-600 hover:text-blue-800 inline-flex items-center gap-1 cursor-pointer"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Inspect</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={9} className="py-12 text-center text-slate-400 font-medium">
                      No observations match the selected filter parameters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Navigation Bar */}
          {data && data.total_pages > 1 && (
            <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <span className="text-slate-500 font-mono">
                Page <span className="font-bold text-slate-800">{page}</span> of{' '}
                <span className="font-bold text-slate-800">{data.total_pages}</span>
              </span>

              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  disabled={!data.has_prev}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>

                <button
                  type="button"
                  disabled={!data.has_next}
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* 3. Evidence-First Right-Side Inspection Drawer */}
        <AnimatePresence>
          {selectedObs && (
            <>
              {/* Backdrop */}
              <motion.div
                variants={drawerBackdropVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                onClick={() => setSelectedObs(null)}
                className="fixed inset-0 bg-slate-900 z-40"
              />
              {/* Drawer Surface */}
              <motion.div
                variants={drawerVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                role="dialog"
                aria-modal="true"
                aria-label="Observation Evidence Record"
                className="fixed inset-y-0 right-0 z-50 w-full sm:max-w-lg bg-white/95 backdrop-blur-xl border-l border-slate-200 shadow-[0_0_40px_rgba(15,23,42,0.1)] flex flex-col justify-between overflow-y-auto"
              >
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900 tracking-tight">
                  Observation Evidence Record
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedObs(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body: Identity → Fare → Flight → Quality → Provenance */}
            <div className="p-6 space-y-6 text-xs divide-y divide-slate-100">
              {/* Step 1: Identity */}
              <div className="space-y-3">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
                  1. OBSERVATION IDENTITY
                </span>
                <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200/80 space-y-2 font-mono">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Observation UUID:</span>
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-slate-800 text-[11px]">
                        {selectedObs.observation_id}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCopy(selectedObs.observation_id)}
                        className="text-slate-400 hover:text-slate-700 cursor-pointer"
                        title="Copy UUID"
                      >
                        {copiedId === selectedObs.observation_id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Corridor Route:</span>
                    <span className="font-bold text-blue-600">{selectedObs.route_id}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Collection Timestamp:</span>
                    <span className="text-slate-700">
                      {selectedObs.collection_timestamp ? new Date(selectedObs.collection_timestamp).toISOString() : '—'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Step 2: Fare Structure & Decomposition */}
              <div className="pt-5 space-y-3">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
                  2. FARE DECOMPOSITION
                </span>
                <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200/80 space-y-2 font-mono">
                  <div className="flex items-center justify-between border-b border-slate-200/60 pb-2">
                    <span className="font-bold text-slate-700">Total Fare:</span>
                    <span className="text-base font-extrabold text-slate-900 mono-number">
                      ₹{selectedObs.total_fare.toFixed(2)} {selectedObs.currency}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Base fare:</span>
                    <span className="text-slate-800 mono-number">
                      {selectedObs.base_fare != null
                        ? `₹${selectedObs.base_fare.toFixed(2)}`
                        : <span className="text-slate-400 font-sans text-xs italic">Not provided by source</span>}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Taxes &amp; Surcharges:</span>
                    <span className="text-slate-800 mono-number">
                      {selectedObs.taxes != null
                        ? `₹${selectedObs.taxes.toFixed(2)}`
                        : <span className="text-slate-400 font-sans text-xs italic">Not provided by source</span>}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Mandatory Fees:</span>
                    <span className="text-slate-800 mono-number">
                      {selectedObs.fees != null
                        ? `₹${selectedObs.fees.toFixed(2)}`
                        : <span className="text-slate-400 font-sans text-xs italic">Not provided by source</span>}
                    </span>
                  </div>
                  {selectedObs.base_fare == null && (
                    <div className="pt-2 border-t border-slate-200/50 text-[11px] text-slate-500 font-sans leading-tight">
                      Total-only observation: Source did not publish separated base fare. AeroCPI ingestion policy strictly prohibits back-solving or estimating components.
                    </div>
                  )}
                </div>
              </div>

              {/* Step 3: Flight Operational Context */}
              <div className="pt-5 space-y-3">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
                  3. FLIGHT OPERATIONAL CONTEXT
                </span>
                <div className="grid grid-cols-2 gap-2.5 font-mono">
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                    <span className="text-slate-400 text-[10px] block">CARRIER</span>
                    <span className="font-bold text-slate-800">{selectedObs.carrier}</span>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                    <span className="text-slate-400 text-[10px] block">CABIN CLASS</span>
                    <span className="font-bold text-slate-800">{selectedObs.cabin}</span>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                    <span className="text-slate-400 text-[10px] block">ADVANCE DAYS</span>
                    <span className="font-bold text-blue-600">T+{selectedObs.advance_purchase_days}</span>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                    <span className="text-slate-400 text-[10px] block">TRAVEL DATE</span>
                    <span className="font-bold text-slate-800">{selectedObs.travel_date || '—'}</span>
                  </div>
                </div>
              </div>

              {/* Step 4: Quality & Validation Diagnostics */}
              <div className="pt-5 space-y-3">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
                  4. QUALITY &amp; VALIDATION DIAGNOSTICS
                </span>
                <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200/80 space-y-2 font-mono">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Validation Status:</span>
                    <span className="font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
                      {selectedObs.validation_status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Index Eligibility:</span>
                    <span className="font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
                      {selectedObs.index_eligibility}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Completeness Profile:</span>
                    <span className="text-emerald-700 font-bold">{selectedObs.quality_status}</span>
                  </div>

                  <div className="pt-1">
                    <span className="text-slate-500 block mb-1">Anomaly Flags:</span>
                    {selectedObs.anomaly_flags && selectedObs.anomaly_flags.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {selectedObs.anomaly_flags.map((f, i) => (
                          <span key={i} className="px-1.5 py-0.5 rounded bg-rose-50 border border-rose-200 text-[10px] text-rose-700">
                            {f}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-400 text-[11px]">Zero anomalous rule flags detected</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Step 5: Provenance & Reproducibility Audit */}
              <div className="pt-5 space-y-3">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
                  5. PROVENANCE &amp; AUDIT TRAIL
                </span>
                <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200/80 space-y-2 font-mono text-[11px]">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Source Adapter:</span>
                    <span className="font-bold text-slate-800">{selectedObs.source}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Manifest SHA-256:</span>
                    <span className="text-slate-600" title={audit.manifest_sha256 || audit.canonical_run_fingerprint}>
                      {(audit.manifest_sha256 || audit.canonical_run_fingerprint).substring(0, 16)}...
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Reproducibility:</span>
                    <span className="font-bold text-emerald-700">{audit.reproducibility_status}</span>
                  </div>
                </div>

                <p className="text-[10px] text-slate-400 leading-normal font-sans pt-2">
                  AeroCPI is an independent real-time airfare price index designed to augment CPI and is not statistically equivalent to CPI.
                </p>
              </div>
            </div>

            {/* Drawer Footer */}
            <div className="p-6 border-t border-slate-100 bg-slate-50/50 flex items-center justify-end">
              <button
                type="button"
                onClick={() => setSelectedObs(null)}
                className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs cursor-pointer shadow-xs"
              >
                Close Inspector
              </button>
            </div>
          </motion.div>
        </>
        )}
      </AnimatePresence>
      </div>
    </div>
  );
};
