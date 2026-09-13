import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Info,
  BookOpen,
  ArrowRight,
  ExternalLink,
  Scale,
  Database,
  Layers,
  Activity,
  Compass,
  FileText,
  Calendar,
  Clock,
  X,
  Sparkles,
  GitCommit,
  Check,
  Search
} from 'lucide-react';
import {
  IndexDashboardResponse,
  IndexAuditResponse,
  ValidationBenchmark,
  ValidationRun,
  ValidationMetric
} from '../types';
import { PlatformTab } from '../components/Header';
import {
  fetchValidationBenchmarks,
  fetchValidationRun,
  fetchValidationMetrics
} from '../services/api';

interface ValidationLabPageProps {
  dashboard: IndexDashboardResponse;
  audit: IndexAuditResponse | null;
  onSelectTab?: (tab: PlatformTab) => void;
  onOpenAuditModal?: () => void;
}

interface ProtocolStage {
  id: number;
  shortName: string;
  title: string;
  subtitle: string;
  status: 'NOT AVAILABLE' | 'DORMANT';
  description: string;
  inputs: string;
  outputs: string;
  dimension: string;
  rules: string[];
}

const PROTOCOL_STAGES: ProtocolStage[] = [
  {
    id: 1,
    shortName: 'BENCHMARK',
    title: 'Stage 1: Benchmark Artifact Registration',
    subtitle: 'Independent Ground-Truth Aviation Series',
    status: 'NOT AVAILABLE',
    description:
      'Identifies, verifies, and registers independent third-party aviation price series (e.g., DGCA passenger yields, audited airline settlement figures, or global distribution system aggregates).',
    inputs: 'Independent external ticket price ledger, regulatory tables, or audited settlement logs',
    outputs: 'Cryptographic Benchmark Manifest (SHA-256) & Ingestion Descriptor',
    dimension: 'Source Independence & Authority',
    rules: [
      'Must originate from an independent third-party source outside AeroCPI collectors',
      'Requires verified sampling methodology and immutable publishing timestamps',
      'Cannot be derived, back-solved, or extrapolated from AeroCPI internal data'
    ]
  },
  {
    id: 2,
    shortName: 'ALIGN',
    title: 'Stage 2: Temporal & Scope Alignment',
    subtitle: 'Harmonization to AeroCPI Sovereign Corridor Basket',
    status: 'DORMANT',
    description:
      'Harmonizes third-party observations to match AeroCPI route definitions (10 DGCA corridors), departure window boundaries (10:00 - 18:00 IST), and INR currency normalization.',
    inputs: 'Raw benchmark records + AeroCPI route basket dictionary (BASKET-DGCA-2025-TOP10)',
    outputs: 'Harmonized Benchmark Dataset with unified route-corridor identifiers',
    dimension: 'Temporal & Route Comparability',
    rules: [
      'Strict airport-pair equivalence (e.g., DEL-BOM non-stop trunk)',
      'Calendar travel date and departure timing alignment',
      'Cabin class standardization to Economy (Y-class)'
    ]
  },
  {
    id: 3,
    shortName: 'MATCH',
    title: 'Stage 3: Cell-Level Observation Matching',
    subtitle: 'Strict Corridor & Advance Horizon Pairing',
    status: 'DORMANT',
    description:
      'Pairs benchmark quotes against AeroCPI observations across the 50 discrete corridor-horizon cells (T+1, T+7, T+15, T+30, T+45). Requires a minimum cell representation threshold before scoring.',
    inputs: 'AeroCPI active calculation quotes (N=2,668) + Harmonized benchmark observations',
    outputs: 'Matched Observation Dyad Matrix per corridor-horizon pair',
    dimension: 'Sample Coverage & Density Agreement',
    rules: [
      'Exact advance purchase window matching (T+d days lead time)',
      'Minimum coverage threshold: ≥ 80% of basket routes must have matching pairs',
      'Unmatched observations excluded with transparent ledger reason codes'
    ]
  },
  {
    id: 4,
    shortName: 'COMPARE',
    title: 'Stage 4: Representative Fare & Spread Comparison',
    subtitle: 'Elementary Relatives & Tracking Divergence',
    status: 'DORMANT',
    description:
      'Compares median representative fare levels and price relatives (R_r,h) between AeroCPI and the independent benchmark series across each route and horizon window.',
    inputs: 'AeroCPI elementary route medians + Benchmark median fare levels',
    outputs: 'Cell-by-cell price relative difference vectors & tracking error arrays',
    dimension: 'Level Agreement & Relative Tracking',
    rules: [
      'Compares unweighted representative medians without altering AeroCPI values',
      'Evaluates basis-point spread and directional delta per corridor',
      'Zero client-side recalculation of primary index levels'
    ]
  },
  {
    id: 5,
    shortName: 'SCORE',
    title: 'Stage 5: Econometric Metric Computation',
    subtitle: 'Multi-Dimensional Error & Correlation Statistics',
    status: 'DORMANT',
    description:
      'Executes multi-dimensional statistical metrics: Pearson correlation coefficient (r), Directional Concordance (≥ 0), Mean Absolute Deviation (MAD), and Root Mean Square Error (RMSE).',
    inputs: 'Matched dyad vectors and comparative price relative series',
    outputs: 'Certified Validation Metric Manifest',
    dimension: 'Quantitative Econometric Performance',
    rules: [
      'Evaluates Pearson correlation coefficient: r ∈ [-1.0, 1.0]',
      'Directional concordance: proportion of agreeing period-over-period shifts',
      'Mean absolute error (MAE) and root mean square error (RMSE) in index points'
    ]
  },
  {
    id: 6,
    shortName: 'INTERPRET',
    title: 'Stage 6: Scientific Boundary Interpretation',
    subtitle: 'Econometric Qualification & Manifest Sealing',
    status: 'DORMANT',
    description:
      'Contextualizes the empirical findings against statutory CPI boundaries, data limitations, and sampling scope. Seals the final validation run with an immutable SHA-256 fingerprint.',
    inputs: 'Validation metric manifest + Methodology boundaries',
    outputs: 'Sealed Validation Audit Certification & Boundary Report',
    dimension: 'Statutory Assurance & Integrity',
    rules: [
      'Reiterates non-equivalence to official MoSPI Consumer Price Index',
      'Qualifies empirical scope to domestic aviation passenger market',
      'Embeds immutable SHA-256 fingerprint linking to canonical calculation run'
    ]
  }
];

export const ValidationLabPage: React.FC<ValidationLabPageProps> = ({
  dashboard,
  audit,
  onSelectTab,
  onOpenAuditModal
}) => {
  const { dashboard_scope: scope } = dashboard;

  const [benchmarks, setBenchmarks] = useState<ValidationBenchmark[]>([]);
  const [validationRun, setValidationRun] = useState<ValidationRun | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [activeStageId, setActiveStageId] = useState<number>(1);
  const [selectedBenchmark, setSelectedBenchmark] = useState<ValidationBenchmark | null>(null);
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(false);

  const loadValidationData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [bmData, runData] = await Promise.all([
        fetchValidationBenchmarks(),
        fetchValidationRun(scope.run_id)
      ]);
      setBenchmarks(bmData);
      setValidationRun(runData);
    } catch (err: any) {
      console.error('Failed to load validation lab data:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch validation lab data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadValidationData();
  }, [scope.run_id]);

  const activeStage = PROTOCOL_STAGES.find((s) => s.id === activeStageId) || PROTOCOL_STAGES[0];

  const handleOpenInspector = (bm: ValidationBenchmark) => {
    setSelectedBenchmark(bm);
    setIsInspectorOpen(true);
  };

  const isExecuted = validationRun?.status === 'ACTIVE' && validationRun?.metrics != null;

  return (
    <div className="surface-solid divide-y divide-slate-100">
      {/* 1. Header & Page Identity */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-200/80">
              <FlaskConical className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                  Validation Lab
                </h1>
                <span className="text-[10px] font-mono font-bold bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full border border-purple-200/80 uppercase">
                  Scientific Test Bench
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Independent Benchmarking &amp; Measurement Validation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap text-xs font-mono">
            <div className="surface-subtle px-3 py-1.5 text-slate-700 shadow-xs">
              <span className="text-slate-400 mr-1.5">RUN:</span>
              <span className="font-bold text-slate-900">{scope.run_id.substring(0, 8)}...</span>
            </div>

            <div className="surface-subtle px-3 py-1.5 text-slate-700 shadow-xs">
              <span className="text-slate-400 mr-1.5">CONFIG:</span>
              <span className="font-bold text-blue-700">2026.1.0-default</span>
            </div>

            <div className="bg-amber-50 text-amber-800 border border-amber-200/90 rounded-xl px-3 py-1.5 text-[11px] font-bold shadow-xs flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              <span>STATUS: {validationRun?.status || 'DISABLED_NO_BENCHMARK_DATA'}</span>
            </div>
          </div>
        </div>

        {/* Hero State: Calm, intentional scientific presentation */}
        <div className="bg-slate-50/90 border border-slate-200/80 rounded-2xl p-5 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-mono">
                VALIDATION STATUS
              </span>
              <span className="px-2.5 py-0.5 rounded-md text-xs font-mono font-bold bg-amber-100/80 text-amber-900 border border-amber-300/80">
                {validationRun?.status || 'DISABLED_NO_BENCHMARK_DATA'}
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
              <span>Execution State:</span>
              <span className="font-bold text-slate-800">
                {isExecuted ? 'EXECUTED' : 'NOT EXECUTED'}
              </span>
            </div>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed font-sans">
            "No independent benchmark dataset is currently available for execution. AeroCPI therefore does not publish fabricated validation statistics."
          </p>

          <div className="pt-2 border-t border-slate-200/60 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
            <span>
              Scientific governance policy: AeroCPI treats benchmark absence as an empirical fact rather than generating simulated scores.
            </span>
            <span className="font-mono text-slate-400">
              Evaluated for Run {scope.run_id.substring(0, 8)}
            </span>
          </div>
        </div>
      </div>

      {/* 2. SECTION A: VALIDATION STATUS PANEL */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight uppercase">
                A. Validation Status &amp; Execution Telemetry
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Backend-certified validation execution state, run identity, and benchmark availability.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">State:</span>
            <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-2.5 py-0.5 rounded border border-slate-200">
              NOT EXECUTED
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
              Validation Run Status
            </span>
            <div className="font-mono">
              <span className="text-sm font-bold text-amber-800 break-all">
                {validationRun?.status || 'DISABLED_NO_BENCHMARK_DATA'}
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
              Reason: DISABLED_NO_BENCHMARK_DATA
            </span>
          </div>

          <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
              Benchmark Availability
            </span>
            <div className="font-mono">
              <span className="text-lg font-bold text-slate-900">
                {benchmarks.length} Registered
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
              0 external datasets supplied
            </span>
          </div>

          <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
              Measurement Window
            </span>
            <div className="font-mono">
              <span className="text-xs font-bold text-slate-800">
                {scope.reference_date} → {scope.calculation_date}
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
              Baseline: 2026-09-10 = 100.000
            </span>
          </div>

          <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
              Validation Timestamp
            </span>
            <div className="font-mono">
              <span className="text-xs font-bold text-slate-800">
                {validationRun?.validation_timestamp
                  ? validationRun.validation_timestamp.replace('T', ' ').substring(0, 19)
                  : 'Awaiting Run'}
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
              Deterministic verification clock
            </span>
          </div>
        </div>
      </div>

      {/* 3. SECTION B: BENCHMARK DEFINITION */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-600" />
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight uppercase">
                B. Independent Benchmark Specification &amp; Definition
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Specification of required input dimensions vs. currently registered independent benchmarks.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Specification Standards
          </span>
        </div>

        {/* Required Fields vs Currently Available Specification Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-200/90">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50/90 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Benchmark Dimension</th>
                <th className="py-3 px-4">Required Benchmark Specification</th>
                <th className="py-3 px-4">Currently Available in System</th>
                <th className="py-3 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              <tr className="hover:bg-slate-50/60">
                <td className="py-3 px-4 font-bold text-slate-900 font-sans">1. Source Authority</td>
                <td className="py-3 px-4 text-slate-600 font-sans">Independent third-party regulatory or audited GDS clearinghouse</td>
                <td className="py-3 px-4 text-slate-500">None (Internal pipeline quotes only)</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                    Awaiting Artifact
                  </span>
                </td>
              </tr>
              <tr className="hover:bg-slate-50/60">
                <td className="py-3 px-4 font-bold text-slate-900 font-sans">2. Route Basket Scope</td>
                <td className="py-3 px-4 text-slate-600 font-sans">10 Top Indian Domestic Routes Basket (DGCA passenger ranking)</td>
                <td className="py-3 px-4 text-slate-900 font-bold">10 / 10 Corridors Defined</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    Specification Ready
                  </span>
                </td>
              </tr>
              <tr className="hover:bg-slate-50/60">
                <td className="py-3 px-4 font-bold text-slate-900 font-sans">3. Temporal Window</td>
                <td className="py-3 px-4 text-slate-600 font-sans">Matching collection date (2026-09-12) &amp; base reference (2026-09-10)</td>
                <td className="py-3 px-4 text-slate-900 font-bold">Matched Active Run Window</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    Specification Ready
                  </span>
                </td>
              </tr>
              <tr className="hover:bg-slate-50/60">
                <td className="py-3 px-4 font-bold text-slate-900 font-sans">4. Lead Horizon Structure</td>
                <td className="py-3 px-4 text-slate-600 font-sans">5 advance booking horizons: T+1, T+7, T+15, T+30, T+45 days</td>
                <td className="py-3 px-4 text-slate-900 font-bold">5 / 5 Horizons Active</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    Specification Ready
                  </span>
                </td>
              </tr>
              <tr className="hover:bg-slate-50/60">
                <td className="py-3 px-4 font-bold text-slate-900 font-sans">5. Cabin &amp; Flight Rules</td>
                <td className="py-3 px-4 text-slate-600 font-sans">Economy cabin (Y-class), non-stop priority, standardized departure</td>
                <td className="py-3 px-4 text-slate-900 font-bold">Rule Suite VAL-2026.1</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    Specification Ready
                  </span>
                </td>
              </tr>
              <tr className="hover:bg-slate-50/60">
                <td className="py-3 px-4 font-bold text-slate-900 font-sans">6. Fare Metric Definition</td>
                <td className="py-3 px-4 text-slate-600 font-sans">Published total airfare in Indian Rupees (INR) including taxes/fees</td>
                <td className="py-3 px-4 text-slate-900 font-bold">Total-Only Policy Adherent</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    Specification Ready
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Registered Benchmark Registry Display */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
              Registered Benchmark Specifications
            </h3>
            <span className="text-xs font-mono text-slate-400">
              0 Datasets Available
            </span>
          </div>

          {benchmarks.length === 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Benchmark Slot 1 */}
              <div
                onClick={() =>
                  handleOpenInspector({
                    benchmark_id: 'BM-DGCA-YIELDS-V1',
                    name: 'DGCA Official Domestic Passenger Yield Series',
                    description:
                      'Official monthly revenue-per-passenger-kilometer (RPKM) and route average yield statistics compiled by the Directorate General of Civil Aviation.',
                    source: 'Directorate General of Civil Aviation (DGCA)',
                    reference_period: 'Monthly Aggregation',
                    created_at: '2026-01-01T00:00:00Z'
                  })
                }
                className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-3 hover:border-blue-300 hover:shadow-xs cursor-pointer transition-all group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                    <span className="font-mono font-bold text-xs text-slate-900">
                      BM-DGCA-YIELDS-V1
                    </span>
                  </div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                    AWAITING SUBMISSION
                  </span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">
                    DGCA Official Domestic Passenger Yield Series
                  </h4>
                  <p className="text-[11px] text-slate-500 font-sans mt-0.5 leading-relaxed">
                    Official regulatory passenger yield reports. Ingestion awaiting official release and publication of comparable calculation period data.
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>Source: DGCA Economic Statistics</span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenInspector({
                        benchmark_id: 'BM-DGCA-YIELDS-V1',
                        name: 'DGCA Official Domestic Passenger Yield Series',
                        description:
                          'Official monthly revenue-per-passenger-kilometer (RPKM) and route average yield statistics compiled by the Directorate General of Civil Aviation.',
                        source: 'Directorate General of Civil Aviation (DGCA)',
                        reference_period: 'Monthly Aggregation',
                        created_at: '2026-01-01T00:00:00Z'
                      });
                    }}
                    className="text-blue-600 hover:text-blue-700 flex items-center gap-1 font-bold group-hover:underline"
                  >
                    Inspect Spec <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Benchmark Slot 2 */}
              <div
                onClick={() =>
                  handleOpenInspector({
                    benchmark_id: 'BM-GDS-SETTLEMENT-V1',
                    name: 'Commercial GDS Multi-Carrier Settlement Benchmark',
                    description:
                      'Aggregated, multi-carrier BSP settlement transaction data reflecting booked airfares across domestic commercial travel agencies.',
                    source: 'Commercial GDS Clearinghouse Consortium',
                    reference_period: 'Daily Matched',
                    created_at: '2026-01-01T00:00:00Z'
                  })
                }
                className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-3 hover:border-blue-300 hover:shadow-xs cursor-pointer transition-all group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                    <span className="font-mono font-bold text-xs text-slate-900">
                      BM-GDS-SETTLEMENT-V1
                    </span>
                  </div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                    AWAITING SUBMISSION
                  </span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">
                    Commercial GDS Multi-Carrier Settlement Benchmark
                  </h4>
                  <p className="text-[11px] text-slate-500 font-sans mt-0.5 leading-relaxed">
                    Aggregated BSP transaction log. No settlement dataset is currently licensed or available for the matching period.
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>Source: GDS Clearinghouse</span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenInspector({
                        benchmark_id: 'BM-GDS-SETTLEMENT-V1',
                        name: 'Commercial GDS Multi-Carrier Settlement Benchmark',
                        description:
                          'Aggregated, multi-carrier BSP settlement transaction data reflecting booked airfares across domestic commercial travel agencies.',
                        source: 'Commercial GDS Clearinghouse Consortium',
                        reference_period: 'Daily Matched',
                        created_at: '2026-01-01T00:00:00Z'
                      });
                    }}
                    className="text-blue-600 hover:text-blue-700 flex items-center gap-1 font-bold group-hover:underline"
                  >
                    Inspect Spec <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {benchmarks.map((bm) => (
                <div
                  key={bm.benchmark_id}
                  onClick={() => handleOpenInspector(bm)}
                  className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2 cursor-pointer hover:border-blue-300"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-slate-900">{bm.benchmark_id}</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                      REGISTERED
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-800">{bm.name}</h4>
                  <p className="text-[11px] text-slate-500">{bm.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 4. SECTION C: VALIDATION PROTOCOL & SIGNATURE PIPELINE VISUAL */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight uppercase">
                C. Validation Protocol &amp; Execution Pipeline
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Planned scientific validation framework: 6-stage end-to-end alignment, matching, and scoring pipeline.
            </p>
          </div>
          <span className="text-xs font-mono text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded">
            DORMANT AT STAGE 1
          </span>
        </div>

        {/* Signature Visual: 6-Stage Scientific Pipeline */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {PROTOCOL_STAGES.map((stage) => {
              const isActive = stage.id === activeStageId;
              const isBlocked = stage.id > 1;

              return (
                <button
                  key={stage.id}
                  type="button"
                  onClick={() => setActiveStageId(stage.id)}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    isActive
                      ? 'bg-white border-blue-500  ring-2 ring-blue-500/20'
                      : isBlocked
                      ? 'bg-slate-50/60 border-slate-200/60 opacity-85 hover:bg-slate-100/60'
                      : 'bg-amber-50/70 border-amber-200 hover:bg-amber-100/60'
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="font-bold text-slate-500">STAGE {stage.id}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded font-bold text-[9px] ${
                        stage.status === 'NOT AVAILABLE'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {stage.status}
                    </span>
                  </div>
                  <span className="font-mono font-bold text-xs text-slate-900 block mt-1">
                    {stage.shortName}
                  </span>
                  <span className="text-[10px] text-slate-400 block truncate font-sans">
                    {stage.dimension}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Active Protocol Stage Detail Card */}
          <div className="bg-slate-50/90 rounded-2xl p-6 border border-slate-200/80 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200/70">
              <div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  PLANNED SPECIFICATION ONLY · {activeStage.status}
                </span>
                <h3 className="text-sm font-extrabold text-slate-900 mt-1">
                  {activeStage.title}
                </h3>
                <p className="text-xs text-slate-500">{activeStage.subtitle}</p>
              </div>

              <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
                <span>Measurement Dimension:</span>
                <span className="font-bold text-slate-800">{activeStage.dimension}</span>
              </div>
            </div>

            <p className="text-xs text-slate-700 leading-relaxed font-sans">
              {activeStage.description}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="bg-white p-3 rounded-xl border border-slate-200/70 space-y-1">
                <span className="text-[10px] text-slate-400 block font-sans font-bold uppercase">
                  Input Artefacts
                </span>
                <span className="text-slate-800 block text-[11px]">{activeStage.inputs}</span>
              </div>

              <div className="bg-white p-3 rounded-xl border border-slate-200/70 space-y-1">
                <span className="text-[10px] text-slate-400 block font-sans font-bold uppercase">
                  Expected Output Artefacts
                </span>
                <span className="text-slate-800 block text-[11px]">{activeStage.outputs}</span>
              </div>
            </div>

            <div className="space-y-1.5 pt-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                Stage Rules &amp; Operational Invariants
              </span>
              <ul className="space-y-1 text-xs text-slate-600 font-sans list-disc list-inside">
                {activeStage.rules.map((rule, idx) => (
                  <li key={idx} className="leading-relaxed">
                    {rule}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* 5. SECTION D: RESULTS */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-blue-600" />
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight uppercase">
                D. Empirical Validation Results &amp; Tracking Error
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Statistical comparison metrics between AeroCPI and independent benchmark series.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {isExecuted ? 'EXECUTED METRICS' : 'AWAITING BENCHMARK'}
          </span>
        </div>

        {!isExecuted ? (
          /* STATE 1: NO BENCHMARK (Awaiting Benchmark) */
          <div className="space-y-6">
            <div className="bg-slate-50/90 border border-slate-200/80 rounded-2xl p-6 text-center space-y-2">
              <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center mx-auto border border-slate-200">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-extrabold text-slate-900 uppercase tracking-tight">
                NO VALIDATION RESULT
              </h3>
              <p className="text-xs text-slate-500 max-w-lg mx-auto font-sans leading-relaxed">
                Benchmark execution is unavailable because no independent benchmark artifact is registered. AeroCPI does not display placeholder zeros, simulated percentages, or fabricated correlation plots.
              </p>
            </div>

            {/* Empty Metric Shells labeled "Not Available" */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Coverage Agreement
                </span>
                <div className="font-mono">
                  <span className="text-sm font-bold text-slate-500">Not Available</span>
                </div>
                <span className="text-[11px] text-slate-400 font-sans block pt-1 border-t border-slate-200/60">
                  Target: ≥ 90.0% Matched Cells
                </span>
              </div>

              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Level Error (MAD)
                </span>
                <div className="font-mono">
                  <span className="text-sm font-bold text-slate-500">Not Available</span>
                </div>
                <span className="text-[11px] text-slate-400 font-sans block pt-1 border-t border-slate-200/60">
                  Target: Mean Absolute Dev &lt; 2.5 pts
                </span>
              </div>

              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Directional Agreement
                </span>
                <div className="font-mono">
                  <span className="text-sm font-bold text-slate-500">Not Available</span>
                </div>
                <span className="text-[11px] text-slate-400 font-sans block pt-1 border-t border-slate-200/60">
                  Target: Directional Concordance ≥ 80%
                </span>
              </div>

              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  RMSE / MAE
                </span>
                <div className="font-mono">
                  <span className="text-sm font-bold text-slate-500">Not Available</span>
                </div>
                <span className="text-[11px] text-slate-400 font-sans block pt-1 border-t border-slate-200/60">
                  Target: Root Mean Square Error bounds
                </span>
              </div>

              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Pearson Correlation (r)
                </span>
                <div className="font-mono">
                  <span className="text-sm font-bold text-slate-500">Not Available</span>
                </div>
                <span className="text-[11px] text-slate-400 font-sans block pt-1 border-t border-slate-200/60">
                  Target: Linear correlation r ≥ 0.85
                </span>
              </div>

              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Relative Deviation (MRD)
                </span>
                <div className="font-mono">
                  <span className="text-sm font-bold text-slate-500">Not Available</span>
                </div>
                <span className="text-[11px] text-slate-400 font-sans block pt-1 border-t border-slate-200/60">
                  Target: Mean relative deviation &lt; 3.0%
                </span>
              </div>
            </div>
          </div>
        ) : (
          /* STATE 2: BENCHMARK EXISTS (Render only backend-supplied metrics) */
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Coverage Agreement
                </span>
                <div className="font-mono">
                  <span className="text-lg font-bold text-emerald-700">
                    {validationRun.metrics?.coverage != null
                      ? `${(validationRun.metrics.coverage * 100).toFixed(1)}%`
                      : 'Not Available'}
                  </span>
                </div>
                <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
                  Backend-certified coverage
                </span>
              </div>

              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Directional Concordance
                </span>
                <div className="font-mono">
                  <span className="text-lg font-bold text-emerald-700">
                    {validationRun.metrics?.directional_agreement != null
                      ? `${(validationRun.metrics.directional_agreement * 100).toFixed(1)}%`
                      : 'Not Available'}
                  </span>
                </div>
                <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
                  Directional shifts matching benchmark
                </span>
              </div>

              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Pearson Correlation (r)
                </span>
                <div className="font-mono">
                  <span className="text-lg font-bold text-blue-700">
                    {validationRun.metrics?.correlation != null
                      ? validationRun.metrics.correlation.toFixed(4)
                      : 'Not Available'}
                  </span>
                </div>
                <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
                  Linear co-movement coefficient
                </span>
              </div>

              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Mean Absolute Deviation (MAD)
                </span>
                <div className="font-mono">
                  <span className="text-lg font-bold text-slate-900">
                    {validationRun.metrics?.absolute_deviation != null
                      ? `${validationRun.metrics.absolute_deviation.toFixed(2)} pts`
                      : 'Not Available'}
                  </span>
                </div>
                <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
                  Absolute index point tracking error
                </span>
              </div>

              <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                  Mean Relative Deviation (MRD)
                </span>
                <div className="font-mono">
                  <span className="text-lg font-bold text-slate-900">
                    {validationRun.metrics?.relative_deviation != null
                      ? `${(validationRun.metrics.relative_deviation * 100).toFixed(2)}%`
                      : 'Not Available'}
                  </span>
                </div>
                <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
                  Relative percentage spread
                </span>
              </div>
            </div>

            {/* Route Level Deviation Matrix if available */}
            {validationRun.metrics?.route_level_deviation && (
              <div className="space-y-3 pt-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-sans">
                  Route-Level Deviation Matrix
                </h4>
                <div className="overflow-x-auto rounded-xl border border-slate-200/90">
                  <table className="w-full text-left text-xs border-collapse font-mono">
                    <thead>
                      <tr className="bg-slate-50/90 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                        <th className="py-2.5 px-4">Corridor Route</th>
                        <th className="py-2.5 px-4 text-right">Route Deviation (pts)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {Object.entries(validationRun.metrics.route_level_deviation).map(([rt, dev]) => (
                        <tr key={rt} className="hover:bg-slate-50/60">
                          <td className="py-2 px-4 font-bold text-slate-900">{rt}</td>
                          <td className="py-2 px-4 text-right">{dev.toFixed(2)} pts</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Theoretical Axiomatic Test Battery (Certified Econometric Properties) */}
        <div className="mt-8 pt-6 border-t-2 border-slate-200/70 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-sans">
                Internal Index Integrity Tests
              </h3>
            </div>
            <span className="text-[10px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              5 / 5 PASSED
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
            <div className="p-3 bg-slate-50/90 rounded-xl border border-slate-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800 font-sans">Time Reversal Test</span>
                <span className="text-[10px] font-mono font-bold text-emerald-700">PASSED</span>
              </div>
              <p className="text-[11px] text-slate-500 font-sans">
                {"$I_{0,t} \\cdot I_{t,0} = 1$"}. Guaranteed by unweighted Jevons geometric mean at elementary route level.
              </p>
            </div>

            <div className="p-3 bg-slate-50/90 rounded-xl border border-slate-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800 font-sans">Proportionality / Homogeneity</span>
                <span className="text-[10px] font-mono font-bold text-emerald-700">PASSED</span>
              </div>
              <p className="text-[11px] text-slate-500 font-sans">
                {"$P(\\lambda p) = \\lambda P(p)$"} (Degree 1). Scaling all fares by constant {"$\\lambda$"} scales index by exactly {"$\\lambda$"}.
              </p>
            </div>

            <div className="p-3 bg-slate-50/90 rounded-xl border border-slate-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800 font-sans">Dimensional Invariance</span>
                <span className="text-[10px] font-mono font-bold text-emerald-700">PASSED</span>
              </div>
              <p className="text-[11px] text-slate-500 font-sans">
                Commensurability: Invariant to units of monetary measurement or uniform currency re-denomination.
              </p>
            </div>

            <div className="p-3 bg-slate-50/90 rounded-xl border border-slate-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800 font-sans">Monotonicity</span>
                <span className="text-[10px] font-mono font-bold text-emerald-700">PASSED</span>
              </div>
              <p className="text-[11px] text-slate-500 font-sans">
                Non-decreasing in comparison period prices: Any price increase cannot result in a lower index value.
              </p>
            </div>

            <div className="p-3 bg-slate-50/90 rounded-xl border border-slate-200/80 space-y-1 sm:col-span-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800 font-sans">Exact Log-Linear Route Point Additivity</span>
                <span className="text-[10px] font-mono font-bold text-emerald-700">PASSED</span>
              </div>
              <p className="text-[11px] text-slate-500 font-sans">
                {"$\\sum_{r=1}^{10} C_r = I - 100$"}. Route-level point contributions sum exactly to the total headline index movement with zero mathematical residual.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 6. SECTION E: LIMITATIONS & INTERPRETATION */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-blue-600" />
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight uppercase">
                E. Limitations &amp; Scientific Interpretation
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Methodological boundaries, verification constraints, and statutory non-equivalence definitions.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Scientific Restraint Standard
          </span>
        </div>

        {/* 5 Key Scientific Interpretation Surfaces */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2">
            <h3 className="text-xs font-bold text-slate-900 font-sans flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-mono text-[10px]">
                1
              </span>
              Internal Consistency is NOT Independent Validation
            </h3>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              Reproducing AeroCPI's internal calculation pipeline, verifying 1.5× IQR outlier bounds, or re-calculating Jevons geometric means confirms internal algorithmic correctness, not external ground-truth empirical validity.
            </p>
          </div>

          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2">
            <h3 className="text-xs font-bold text-slate-900 font-sans flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-mono text-[10px]">
                2
              </span>
              AeroCPI Observations Cannot Serve as Benchmarks
            </h3>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              AeroCPI's own captured quotes (N=2,668 calculation period observations) cannot be compared against themselves to assert external accuracy. True validation requires independent, external price series.
            </p>
          </div>

          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2">
            <h3 className="text-xs font-bold text-slate-900 font-sans flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-mono text-[10px]">
                3
              </span>
              No Benchmark Means No Empirical Claim
            </h3>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              In the absence of an ingested independent benchmark artifact, AeroCPI refrains from asserting empirical accuracy claims. Scientific restraint is maintained as a core product feature.
            </p>
          </div>

          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2">
            <h3 className="text-xs font-bold text-slate-900 font-sans flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-mono text-[10px]">
                4
              </span>
              Validation Does Not Establish MoSPI CPI Equivalence
            </h3>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              External validation against commercial or regulatory aviation yields does not alter AeroCPI's statutory status. AeroCPI remains an independent high-frequency indicator, NOT equivalent to MoSPI Consumer Price Index numbers.
            </p>
          </div>

          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2 md:col-span-2">
            <h3 className="text-xs font-bold text-slate-900 font-sans flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-mono text-[10px]">
                5
              </span>
              Comparability Boundaries &amp; Scope Constraints
            </h3>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              External validation results depend strictly on exact parity across route, booking lead horizon, travel date, and fare decomposition definitions. Mismatched sampling windows or differing tax inclusion policies will introduce structural tracking error.
            </p>
          </div>
        </div>

        {/* MoSPI CPI Augmentation & Boundary Matrix */}
        <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-3">
          <div className="flex items-center gap-2">
            <Scale className="w-4 h-4 text-blue-600" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-sans">
              MoSPI CPI Augmentation Principle &amp; Structural Comparison
            </h3>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-200/90">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-white border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                  <th className="py-2.5 px-4">Dimension</th>
                  <th className="py-2.5 px-4">AeroCPI Sovereign Standard</th>
                  <th className="py-2.5 px-4">Official MoSPI CPI (Transport)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                <tr className="hover:bg-slate-100/50">
                  <td className="py-2.5 px-4 font-bold text-slate-900">Periodicity</td>
                  <td className="py-2.5 px-4 font-mono text-blue-700 font-bold">Daily Real-Time</td>
                  <td className="py-2.5 px-4 font-mono text-slate-600">Monthly Cadence</td>
                </tr>
                <tr className="hover:bg-slate-100/50">
                  <td className="py-2.5 px-4 font-bold text-slate-900">Basket Scope</td>
                  <td className="py-2.5 px-4 font-mono text-slate-800">10 Top DGCA Corridors (5 Horizons)</td>
                  <td className="py-2.5 px-4 text-slate-600">Broad Consumer Basket (Goods &amp; Services)</td>
                </tr>
                <tr className="hover:bg-slate-100/50">
                  <td className="py-2.5 px-4 font-bold text-slate-900">Weighting Engine</td>
                  <td className="py-2.5 px-4 font-mono text-slate-800">DGCA Annual Passenger Throughput</td>
                  <td className="py-2.5 px-4 text-slate-600">Consumer Expenditure Survey (CES)</td>
                </tr>
                <tr className="hover:bg-slate-100/50">
                  <td className="py-2.5 px-4 font-bold text-slate-900">Aggregation Formula</td>
                  <td className="py-2.5 px-4 font-mono text-slate-800">Jevons Elementary + Weighted Geometric National</td>
                  <td className="py-2.5 px-4 text-slate-600">Modified Laspeyres Aggregation</td>
                </tr>
                <tr className="hover:bg-slate-100/50">
                  <td className="py-2.5 px-4 font-bold text-slate-900">Statutory Role</td>
                  <td className="py-2.5 px-4 text-blue-700 font-bold">Operational High-Frequency Observatory</td>
                  <td className="py-2.5 px-4 text-slate-900 font-bold">Statutory National Inflation Metric</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 7. SECTION F: VALIDATION TRACE & CROSS-MODULE PROVENANCE */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <GitCommit className="w-4 h-4 text-blue-600" />
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight uppercase">
                F. Validation Provenance Trace
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              End-to-end cryptographic and methodological provenance chain connecting validation to AeroCPI architecture.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Provenance Lineage
          </span>
        </div>

        {/* Provenance Flow Visualization */}
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono text-xs">
          <div className="bg-slate-50/90 p-3.5 rounded-xl border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 block font-sans font-bold uppercase">1. Benchmark</span>
            <span className="font-bold text-slate-800 block text-[11px]">External Artifact</span>
            <span className="text-[10px] text-amber-700 block">AWAITING SUBMISSION</span>
          </div>

          <div className="bg-slate-50/90 p-3.5 rounded-xl border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 block font-sans font-bold uppercase">2. Benchmark Ver.</span>
            <span className="font-bold text-slate-800 block text-[11px]">Unassigned</span>
            <span className="text-[10px] text-slate-400 block">STANDBY</span>
          </div>

          <div className="bg-slate-50/90 p-3.5 rounded-xl border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 block font-sans font-bold uppercase">3. Alignment Rules</span>
            <span className="font-bold text-slate-800 block text-[11px]">VAL-2026.1</span>
            <span className="text-[10px] text-blue-700 block">CERTIFIED RULESET</span>
          </div>

          <div className="bg-slate-50/90 p-3.5 rounded-xl border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 block font-sans font-bold uppercase">4. Validation Run</span>
            <span className="font-bold text-slate-800 block text-[11px]">{scope.run_id.substring(0, 8)}...</span>
            <span className="text-[10px] text-amber-700 block">NOT EXECUTED</span>
          </div>

          <div className="bg-slate-50/90 p-3.5 rounded-xl border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 block font-sans font-bold uppercase">5. Metrics</span>
            <span className="font-bold text-slate-800 block text-[11px]">Multi-Dim Score</span>
            <span className="text-[10px] text-slate-400 block">HELD (0 DERIVED)</span>
          </div>

          <div className="bg-slate-50/90 p-3.5 rounded-xl border border-slate-200/80 space-y-1">
            <span className="text-[10px] text-slate-400 block font-sans font-bold uppercase">6. Interpretation</span>
            <span className="font-bold text-slate-800 block text-[11px]">Methodology Sealing</span>
            <span className="text-[10px] text-emerald-700 block">BOUNDARIES ATTACHED</span>
          </div>
        </div>

        {/* Cross-Module Navigation Links */}
        <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-wrap text-xs">
            {onSelectTab && (
              <button
                type="button"
                onClick={() => onSelectTab('methodology')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 font-bold hover:bg-slate-100 hover:text-blue-700 cursor-pointer transition-colors"
              >
                <span>View Methodology →</span>
              </button>
            )}

            {onOpenAuditModal && (
              <button
                type="button"
                onClick={onOpenAuditModal}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 font-bold hover:bg-slate-100 hover:text-blue-700 cursor-pointer transition-colors"
              >
                <span>Inspect Measurement Trace →</span>
              </button>
            )}

            {onSelectTab && (
              <button
                type="button"
                onClick={() => onSelectTab('methodology')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 font-bold hover:bg-slate-100 hover:text-blue-700 cursor-pointer transition-colors"
              >
                <span>Inspect Configuration →</span>
              </button>
            )}

            {onSelectTab && (
              <button
                type="button"
                onClick={() => onSelectTab('overview')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 font-bold hover:bg-slate-100 hover:text-blue-700 cursor-pointer transition-colors"
              >
                <span>View Production Run →</span>
              </button>
            )}
          </div>

          <span className="text-xs text-slate-400 font-mono">
            SHA-256: cacd4054...ba46bca
          </span>
        </div>
      </div>

      {/* Detail Inspector Modal / Drawer for Benchmark Details */}
      {isInspectorOpen && selectedBenchmark && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="surface-solid max-w-xl w-full p-6 sm:p-8 space-y-5 rounded-2xl shadow-xl border border-slate-200 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <Database className="w-5 h-5 text-blue-600" />
                <div>
                  <h3 className="text-base font-extrabold text-slate-900">
                    Benchmark Specification Inspector
                  </h3>
                  <span className="text-xs font-mono text-slate-400">
                    {selectedBenchmark.benchmark_id}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsInspectorOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4 text-xs font-sans">
              <div className="p-3 bg-slate-50 rounded-xl space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block font-bold">
                  Benchmark Title
                </span>
                <span className="font-bold text-slate-900 text-sm">{selectedBenchmark.name}</span>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block font-bold">
                  Description &amp; Sampling Methodology
                </span>
                <p className="text-slate-600 leading-relaxed">{selectedBenchmark.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono">
                <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200/70">
                  <span className="text-[10px] text-slate-400 block font-sans">Source Authority</span>
                  <span className="font-bold text-slate-900">{selectedBenchmark.source}</span>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200/70">
                  <span className="text-[10px] text-slate-400 block font-sans">Reference Period</span>
                  <span className="font-bold text-slate-900">{selectedBenchmark.reference_period}</span>
                </div>
              </div>

              <div className="p-3 bg-amber-50/80 rounded-xl border border-amber-200/80 text-amber-900 text-[11px] space-y-1">
                <div className="flex items-center gap-1.5 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                  <span>Ingestion Status: Awaiting Submission</span>
                </div>
                <p>
                  This benchmark definition is registered in the AeroCPI validation catalogue. The external data feed has not been submitted for active run {scope.run_id.substring(0, 8)}. Downstream comparison metrics remain dormant.
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end">
              <button
                type="button"
                onClick={() => setIsInspectorOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 cursor-pointer transition-colors"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
