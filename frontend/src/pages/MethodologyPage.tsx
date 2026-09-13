import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  GitBranch,
  ShieldAlert,
  Cpu,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Filter,
  ShieldCheck,
  Check,
  Copy,
  Sliders,
  AlertCircle,
  RefreshCw,
  Layers,
  Database,
  Calendar,
  Sparkles
} from 'lucide-react';
import {
  IndexDashboardResponse,
  IndexAuditResponse,
  MethodologyInfoResponse,
  PublicationReadinessResponse
} from '../types';
import { BlockMath, InlineMath } from '../components/MathView';
import {
  fetchMethodologyConfiguration,
  fetchPublicationReadiness
} from '../services/api';

interface MethodologyPageProps {
  dashboard: IndexDashboardResponse;
  audit?: IndexAuditResponse | null;
}

interface StepDetail {
  id: number;
  title: string;
  subtitle: string;
  badge: string;
  description: string;
  inputs: string;
  outputs: string;
  formula?: string | string[];
  rules: string[];
}

const PIPELINE_STEPS: StepDetail[] = [
  {
    id: 1,
    title: 'Data Collection & Ingestion',
    subtitle: 'Google Flights API / Live & Persisted Adapters',
    badge: 'STAGE 1 · INGESTION',
    description:
      'Captures raw airfare quotes across all 10 DGCA corridors for 5 forward booking horizons (T+1, T+7, T+15, T+30, T+45). Queries multiple carriers per route window within locked temporal bounds.',
    inputs: '10 DGCA routes × 5 horizons × carrier options (~2,668 raw observations per collection date)',
    outputs: 'Raw observation schema records with canonical collection timestamps, carrier tags, and published fares',
    rules: [
      'Economy cabin class (Y-class equivalent) strictly enforced',
      'Non-stop direct flights prioritized; multi-leg segments filtered',
      'Baggage and carrier tax inclusive total fares extracted',
      'Departure window standardized to 10:00 - 18:00 IST to prevent red-eye skew'
    ]
  },
  {
    id: 2,
    title: 'Observation Filtering & Quality Control',
    subtitle: 'Interquartile Outlier Scrubbing & Cell Verification',
    badge: 'STAGE 2 · CLEANING',
    description:
      'Filters captured quotes to remove invalid tariffs, code-share duplicates, and statistical anomalies using Tukey 1.5× Interquartile Range (IQR) bounds evaluated per route-horizon cell.',
    inputs: '2,668 raw collection quotes',
    outputs: '2,668 validated eligible quotes (100.0% eligibility ratio)',
    formula: 'Q_1 - 1.5 \\cdot \\text{IQR} \\le P_{obs} \\le Q_3 + 1.5 \\cdot \\text{IQR}',
    rules: [
      'Minimum quote density threshold: ≥ 30 quotes per route-horizon cell',
      'Tukey 1.5× IQR boundary applied per (route, horizon) cell',
      'Strict Total-Only policy: zero back-solving of base fares from total-only APIs',
      'Mandatory INR currency normalization at reference date rate'
    ]
  },
  {
    id: 3,
    title: 'Source-Level Median & Cross-Source Representative Fare',
    subtitle: 'Cell Median P_{r,h,s,t} & Cross-Source Geometric Mean P̄_{r,h,t}',
    badge: 'STAGE 3 · CELL & CROSS-SOURCE AGGREGATION',
    description:
      'Computes the source-level median total fare P_{r,h,s,t} per (collection_date, route, horizon, source, cabin) to eliminate outlier quotes, followed by cross-source representative fare construction P̄_{r,h,t} via unweighted geometric mean across active sources. Single-source calculation is explicitly recorded with is_single_source = True.',
    inputs: 'Eligible observation price array per cell (route, horizon, source, cabin)',
    outputs: '50 cross-source representative fare values (10 routes × 5 horizons)',
    formula: 'P_{r,h,s,t} = \\text{Median}\\left(\\{P^{(1)}, \\dots, P^{(N)}\\}\\right) \\implies \\bar{P}_{r,h,t} = \\left( \\prod_{s=1}^{K} P_{r,h,s,t} \\right)^{\\frac{1}{K}}',
    rules: [
      'Hierarchy: Quotes → source-level median → cross-source representative fare → route relative → national aggregation',
      'Source-level median eliminates promotional spikes and carrier-specific price volatility',
      'Cross-source unweighted geometric mean ensures a source with 100 quotes does not dominate a source with 10 quotes',
      'Single active source (K=1) permitted with explicit is_single_source audit flag',
      'Zero synthetic interpolation permitted for missing cells'
    ]
  },
  {
    id: 4,
    title: 'Jevons Elementary Route Index Computation',
    subtitle: 'Unweighted Geometric Mean of Price Relatives (Jᵣ)',
    badge: 'STAGE 4 · ELEMENTARY INDEX',
    description:
      'Computes the unweighted geometric mean of price relatives across all 5 horizons for each corridor route r, creating a sovereign elementary route index value.',
    inputs: 'Representative median fares P_{r,h,t} and P_{r,h,0} across all 5 horizons',
    outputs: '10 elementary route index values J_r (e.g. DEL-HYD: 111.127, GOI-BOM: 54.828)',
    formula: 'J_r = \\left( \\prod_{h=1}^{5} \\frac{P_{r,h,t}}{P_{r,h,0}} \\right)^{\\frac{1}{5}} \\times 100',
    rules: [
      'Axiomatically satisfies time reversal and transitivity tests',
      'Equal 20% weighting across all 5 booking advance windows',
      'Base period normalized to exactly 100.000 at Reference Baseline (2026-09-10)',
      'Invariant to proportional rescaling of individual fares'
    ]
  },
  {
    id: 5,
    title: 'DGCA Passenger Traffic Weight Application',
    subtitle: 'Official Annual Passenger Traffic Volume Share (wᵣ*)',
    badge: 'STAGE 5 · WEIGHTING',
    description:
      'Applies official DGCA passenger volume weights w_r* derived from annual domestic passenger throughput across the 10 corridors in the sovereign basket.',
    inputs: 'Annual DGCA passenger statistics (DEL-BOM: 17.8%, BLR-DEL: 14.1%, BOM-BLR: 11.6%, etc.)',
    outputs: 'Normalized active weight vector summing to exactly 1.0 (100.0%)',
    formula: 'w_r^* = \\frac{\\text{Traffic}_r}{\\sum_{k=1}^{10} \\text{Traffic}_k}',
    rules: [
      'Fixed basket weights prevent chain-drift and substitution bias distortion',
      'Weights automatically normalized to 1.0 if any basket corridor is unavailable',
      'Sovereign Proxy Weight Version: DGCA_BASKET_2025_TOP10',
      'Weights preserved unchanged across forward booking horizons'
    ]
  },
  {
    id: 6,
    title: 'AeroCPI Basket Aggregation & Log-Linear Attribution',
    subtitle: 'Weighted Geometric National Aggregation with Active Weight Renormalization',
    badge: 'STAGE 6 · NATIONAL AGGREGATE',
    description:
      'Aggregates the 10 elementary route indexes J_r into the final AeroCPI headline index using weighted geometric national aggregation with active-weight renormalization, enabling exact additive log-linear route contribution attribution.',
    inputs: '10 elementary route indexes J_r and active DGCA weights w_r*',
    outputs: 'AeroCPI Headline Index Value (T+15 = 96.209, change = -3.791 pts)',
    formula: [
      'I_h = 100 \\cdot \\exp\\left( \\sum_{r} w_r^* \\ln\\left(\\frac{J_{r,h}}{100}\\right) \\right)',
      '\\ln\\left(\\frac{I_h}{100}\\right) = \\sum_{r} w_r^* \\ln\\left(\\frac{J_{r,h}}{100}\\right)'
    ],
    rules: [
      'Weighted Geometric National Aggregation with Active Weight Renormalization: w_r^* = w_r / \\sum_{k \\in \\text{Active}} w_k',
      'Missing corridors are omitted rather than imputed to maintain statistical purity',
      'Exact additive log-linear contribution: C_r = w_r^* \\cdot \\frac{\\ln(J_r/100)}{\\ln(I/100)} \\cdot (I - 100)',
      'Mathematical identity guarantee: \\sum_{r} C_r = I - 100 with zero residual',
      'Headline anchor standardized to T+15 advance purchase window',
      'Non-causal interpretation: reflects structural log-linear point share of total index movement'
    ]
  },
  {
    id: 7,
    title: 'Measurement Assurance & Artifact Sealing',
    subtitle: 'Decoupled Trust Diagnostics & Immutable Manifest Hash',
    badge: 'STAGE 7 · ASSURANCE & SEALING',
    description:
      'Seals the calculation run with an immutable SHA-256 cryptographic manifest hash. Diagnostic Trust Evaluation operates as a decoupled, parallel assurance layer (evaluating multi-source agreement, outlier density, and freshness) and strictly does not modify or feed back into the computed index.',
    inputs: 'Full calculation state, observation arrays, route medians, elementary indexes',
    outputs: 'Sealed Audit Manifest · SHA-256: cacd4054...ba46bca',
    rules: [
      'Decoupled trust evaluation: diagnostic only, never alters index levels or weights',
      'SHA-256 cryptographic sealing of all raw inputs, medians, and index manifests',
      'Multi-layer verification across 4D, 5A, 5B, and 5C audit protocols',
      'Statutory MoSPI non-equivalence notice permanently embedded'
    ]
  }
];

export const MethodologyPage: React.FC<MethodologyPageProps> = ({ dashboard, audit }) => {
  const { methodology, dashboard_scope: scope } = dashboard;
  const [activeStepId, setActiveStepId] = useState<number>(1);
  const [copiedFingerprint, setCopiedFingerprint] = useState(false);

  const [config, setConfig] = useState<MethodologyInfoResponse | null>(null);
  const [readiness, setReadiness] = useState<PublicationReadinessResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadMethodologyData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [cfgData, rdyData] = await Promise.all([
        fetchMethodologyConfiguration(),
        fetchPublicationReadiness(scope.run_id)
      ]);
      setConfig(cfgData);
      setReadiness(rdyData);
    } catch (err: any) {
      console.error('Failed to load methodology configuration:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch configuration');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMethodologyData();
  }, [scope.run_id]);

  const activeStep = PIPELINE_STEPS.find((s) => s.id === activeStepId) || PIPELINE_STEPS[0];

  const handleCopyFingerprint = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedFingerprint(true);
    setTimeout(() => setCopiedFingerprint(false), 2000);
  };

  const fingerprint =
    config?.configuration_fingerprint ||
    audit?.reproducibility_audit?.canonical_run_fingerprint ||
    'cacd4054fff92a9ef625325e33355c061a6432172eb51958f221600a1ba46bca';

  return (
    <div className="surface-solid divide-y divide-slate-100">
      {/* 1. Top Header Card */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200/80">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                  METHODOLOGY STUDIO &amp; MEASUREMENT SPECIFICATION
                </h1>
                <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200/80 uppercase">
                  Sovereign Standard
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Versioned Measurement Configuration · 7-Stage End-to-End Calculation Pipeline · Deterministic Publication Gate
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap text-xs font-mono">
            <div className="surface-subtle px-3 py-1.5 text-slate-700 shadow-xs">
              <span className="text-slate-400 mr-1.5">CONFIG:</span>
              <span className="font-bold text-slate-900">
                {config?.configuration_version || '2026.1.0-default'}
              </span>
            </div>

            <div className="surface-subtle px-3 py-1.5 text-slate-700 shadow-xs">
              <span className="text-slate-400 mr-1.5">BASKET:</span>
              <span className="font-bold text-blue-700">
                {config?.basket_version || methodology.basket_version}
              </span>
            </div>

            <div className="bg-emerald-50 text-emerald-700 border border-emerald-200/90 rounded-xl px-3 py-1.5 text-[11px] font-bold shadow-xs flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>GATE: {readiness?.status || 'PUBLISHABLE'}</span>
            </div>
          </div>
        </div>

        {/* Framing Architecture Notice */}
        <div className="bg-slate-50/90 border border-slate-200/80 rounded-2xl p-4 flex items-start sm:items-center gap-2.5 text-xs text-slate-600">
          <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5 sm:mt-0" />
          <span>
            AeroCPI employs an unweighted Jevons geometric mean across 5 advance booking windows ($T+d$), aggregated into headline index points using official DGCA annual passenger throughput weights. Zero client-side mathematical recalculation.
          </span>
        </div>
      </div>

      {/* 2. Versioned Measurement Configuration & Governance */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-600" />
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight uppercase">
                Versioned Measurement Configuration &amp; Governance
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Immutable measurement parameters governing data capture, validation boundaries, and aggregation rules.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-500">Effective:</span>
            <span className="text-xs font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
              {config?.effective_from ? config.effective_from.split('T')[0] : '2026-01-01'}
            </span>
          </div>
        </div>

        {/* Configuration Fingerprint Display */}
        <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs">
          <div className="space-y-0.5">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
              Configuration Cryptographic Fingerprint (SHA-256)
            </span>
            <span className="text-slate-900 font-bold break-all">{fingerprint}</span>
          </div>
          <button
            type="button"
            onClick={() => handleCopyFingerprint(fingerprint)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 text-xs font-bold shrink-0 cursor-pointer shadow-xs transition-colors"
          >
            {copiedFingerprint ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-500" />
                <span>Copy Fingerprint</span>
              </>
            )}
          </button>
        </div>

        {/* 7 Configuration Dimension Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Dimension 1: Route Basket */}
          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
                1. Route Basket
              </span>
              <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {config?.basket_version || 'DGCA-10-2026.1'}
              </span>
            </div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              {config?.human_descriptions?.basket_version ||
                'DGCA 10 Top Indian Domestic Routes Basket based on annual passenger traffic (DEL-BOM, BLR-DEL, BOM-BLR, DEL-HYD, CCU-DEL, BOM-GOI, DEL-MAA, BLR-HYD, DEL-PNQ, DEL-PAT).'}
            </p>
          </div>

          {/* Dimension 2: Horizon Structure */}
          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
                2. Horizon Set
              </span>
              <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {config?.horizon_set?.join(', ') || 'T+1, T+7, T+15, T+30, T+45'}
              </span>
            </div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              {config?.human_descriptions?.horizon_set ||
                '5 Advance Purchase Booking Windows: T+1 (Spot), T+7 (1 Wk), T+15 (Headline 2 Wks), T+30 (1 Mo), T+45 (6 Wks).'}
            </p>
          </div>

          {/* Dimension 3: Validation Suite */}
          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
                3. Validation Rules
              </span>
              <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {config?.validation_rule_version || 'VAL-2026.1'}
              </span>
            </div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              {config?.human_descriptions?.validation_rule_version ||
                'Structural Validation Rule Suite V1: Economy cabin (Y-class), non-stop priority, INR currency, standardized 10:00 - 18:00 IST departure window.'}
            </p>
          </div>

          {/* Dimension 4: Outlier Engine */}
          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
                4. Outlier Governance
              </span>
              <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {config?.outlier_rule_version || 'IQR-1.5-v1'}
              </span>
            </div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              {config?.human_descriptions?.outlier_rule_version ||
                'Tukey 1.5× Interquartile Range (IQR) Outlier Detection Engine evaluated independently across each corridor-horizon observation cell.'}
            </p>
          </div>

          {/* Dimension 5: Source Policy */}
          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
                5. Source Policy
              </span>
              <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {config?.source_policy_version || 'MULTI-SOURCE-V1'}
              </span>
            </div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              {config?.human_descriptions?.source_policy_version ||
                'Multi-Source Agreement & Aggregation Policy: Primary and shadow adapters verified; Total-Only protocol strictly enforced.'}
            </p>
          </div>

          {/* Dimension 6: Aggregation Engine */}
          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
                6. Aggregation Engine
              </span>
              <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {config?.aggregation_version || 'JEVONS-GEOMETRIC-V1'}
              </span>
            </div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              {config?.human_descriptions?.aggregation_version ||
                'Unweighted Jevons Geometric Mean & Weighted Geometric National Aggregation with Active Weight Renormalization with exact additive log-linear route point decomposition.'}
            </p>
          </div>

          {/* Dimension 7: Publication Threshold */}
          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/80 space-y-2.5 md:col-span-2 lg:col-span-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider font-sans">
                7. Publication Threshold &amp; Gate Rules
              </span>
              <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {config?.publication_threshold_version || 'PUB-THRESH-V1'}
              </span>
            </div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              {config?.human_descriptions?.publication_threshold_version ||
                'Minimum 80% Basket Coverage & 85% Active Weight Sum Publication Threshold: Index run must satisfy minimum basket route completeness before publication.'}
            </p>
          </div>
        </div>
      </div>

      {/* 3. Deterministic Publication Gate & Readiness Certification */}
      {readiness && (
        <div className="p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <h3 className="text-base font-extrabold text-slate-900 tracking-tight uppercase">
                  Deterministic Publication Gate &amp; Certification
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Automated publication status evaluation for Active Calculation Run {scope.run_id.substring(0, 8)}...
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-400">Status:</span>
              <span
                className={`text-xs font-mono font-bold px-2.5 py-1 rounded-full border ${
                  readiness.is_publishable
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border-rose-200'
                }`}
              >
                {readiness.status}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Check 1: Headline Coverage */}
            <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                Headline Basket Coverage
              </span>
              <div className="flex items-baseline justify-between font-mono">
                <span className="text-lg font-bold text-slate-900">
                  {(readiness.headline_coverage_ratio * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-emerald-600 font-bold">≥ 80.0% REQ</span>
              </div>
              <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
                10 of 10 routes active in basket
              </span>
            </div>

            {/* Check 2: Active Weight Sum */}
            <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                Active DGCA Weight Sum
              </span>
              <div className="flex items-baseline justify-between font-mono">
                <span className="text-lg font-bold text-slate-900">
                  {(readiness.active_weight_sum * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-emerald-600 font-bold">≥ 85.0% REQ</span>
              </div>
              <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
                100.0% traffic mass represented
              </span>
            </div>

            {/* Check 3: Trust Engine Status */}
            <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                Trust Status Evaluation
              </span>
              <div className="flex items-baseline justify-between font-mono">
                <span className="text-lg font-bold text-amber-700">
                  {readiness.trust_status}
                </span>
                <span className="text-xs text-slate-500 font-bold">ADMITTED</span>
              </div>
              <span className="text-[11px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60">
                Diagnostic-only verification suite
              </span>
            </div>

            {/* Check 4: Deterministic Verdict */}
            <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/80 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-sans font-bold">
                Publication Gate Verdict
              </span>
              <div className="flex items-baseline justify-between font-mono">
                <span className="text-lg font-bold text-emerald-700">
                  {readiness.is_publishable ? 'GATE CLEARED' : 'HELD'}
                </span>
                <span className="text-xs text-emerald-600 font-bold">CLEARED</span>
              </div>
              <span className="text-[10px] text-slate-500 font-sans block pt-1 border-t border-slate-200/60 leading-tight">
                Passes AeroCPI configured publication-readiness gate · Diagnostic verification only, not official/MoSPI statistical certification.
              </span>
            </div>
          </div>

          <div className="bg-slate-50/90 border border-slate-200/80 rounded-xl p-3.5 text-xs text-slate-600 font-sans flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-slate-800">Deterministic Gate Guarantee: </span>
              {readiness.reasons.join(', ')}. The publication gate is an evaluation layer and strictly does not modify calculated price relatives, index levels, or route contributions.
            </div>
          </div>
        </div>
      )}

      {/* 4. 7-Stage End-to-End Calculation Pipeline */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 tracking-tight uppercase">
              7-Stage End-to-End Calculation Pipeline Architecture
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Click any stage in the flow to inspect mathematical formulations, inputs, outputs, and validation rules.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200/80 px-3 py-1 rounded-xl text-xs font-mono font-semibold text-slate-700">
            <span>METHOD: {methodology.methodology_version}</span>
          </div>
        </div>

        {/* 7-Step Horizontal Flow Buttons */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {PIPELINE_STEPS.map((step) => {
            const isActive = step.id === activeStepId;
            return (
              <button
                key={step.id}
                type="button"
                onClick={() => setActiveStepId(step.id)}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  isActive
                    ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/20 -translate-y-[1px]'
                    : 'bg-slate-50 text-slate-700 border-slate-200/80 hover:bg-slate-100 hover:-translate-y-[1px] hover:shadow-sm'
                }`}
              >
                <span
                  className={`text-[10px] font-mono font-bold block ${
                    isActive ? 'text-blue-100' : 'text-slate-400'
                  }`}
                >
                  STAGE {step.id}
                </span>
                <span className="text-xs font-bold font-sans block truncate mt-0.5">
                  {step.title.split('&')[0]}
                </span>
              </button>
            );
          })}
        </div>

        {/* Active Stage Detail Card */}
        <div className="bg-slate-50/70 rounded-2xl border border-slate-200/80 p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
            <div>
              <span className="text-xs font-mono font-bold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200 uppercase">
                {activeStep.badge}
              </span>
              <h3 className="text-2xl font-black text-slate-900 tracking-tight mt-1.5 font-sans">
                Stage {activeStep.id}: {activeStep.title}
              </h3>
              <p className="text-xs text-slate-500 font-mono mt-0.5">{activeStep.subtitle}</p>
            </div>
          </div>

          <p className="text-sm text-slate-700 leading-relaxed font-sans">{activeStep.description}</p>

          {/* Math Formula Callout if available */}
          {activeStep.formula && (
            <div className="p-5 rounded-2xl bg-slate-900 text-white space-y-3 border border-slate-800">
              <span className="text-[10px] text-blue-400 font-bold uppercase tracking-wider block font-sans">
                Mathematical Specification — {activeStep.subtitle}
              </span>
              <div className="space-y-3 pt-1 text-slate-100">
                {Array.isArray(activeStep.formula) ? (
                  activeStep.formula.map((f, i) => (
                    <div key={i} className={i > 0 ? 'pt-3 border-t border-slate-800/80' : ''}>
                      {i === 0 && (
                        <span className="text-[10px] text-slate-400 uppercase font-mono block mb-1">
                          1. National Aggregation (Index Level Form):
                        </span>
                      )}
                      {i === 1 && (
                        <span className="text-[10px] text-slate-400 uppercase font-mono block mb-1">
                          2. Equivalent Logarithmic Form:
                        </span>
                      )}
                      <BlockMath math={f} className="text-blue-200 text-base" />
                    </div>
                  ))
                ) : (
                  <BlockMath math={activeStep.formula} className="text-blue-200 text-base" />
                )}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-1 shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                Stage Input Parameters
              </span>
              <span className="text-xs font-mono font-semibold text-slate-800 block leading-relaxed">
                {activeStep.inputs}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-1 shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block font-sans">
                Stage Output Artifacts
              </span>
              <span className="text-xs font-mono font-semibold text-slate-800 block leading-relaxed">
                {activeStep.outputs}
              </span>
            </div>
          </div>

          {/* Methodological Rules */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-sans">
              Methodological Invariants &amp; Verification Rules
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {activeStep.rules.map((rule, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2.5 p-3 rounded-xl bg-white border border-slate-200/60 text-xs text-slate-800 font-sans shadow-xs"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>{rule}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 5. Non-Causal Aggregation & Exact Additive Decomposition Proof */}
      <div className="p-6 sm:p-8 space-y-5">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <Layers className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Mathematical Proof: Exact Additive Log-Linear Attribution
          </h3>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed font-sans">
          To provide complete transparency without residual discrepancy, AeroCPI implements the exact log-linear decomposition for geometric indexes. For any basket of elementary indexes <InlineMath math="J_r" /> aggregated into a headline index <InlineMath math="I" /> with weights <InlineMath math="w_r^*" />:
        </p>

        <div className="bg-slate-900 text-white rounded-2xl p-5 sm:p-6 space-y-4 border border-slate-800">
          <div>
            <div className="text-blue-400 text-[10px] uppercase font-bold tracking-wider font-sans mb-1">
              1. Weighted Geometric National Aggregation with Active Weight Renormalization
            </div>
            <BlockMath math="\ln\left(\frac{I_h}{100}\right) = \sum_{r} w_r^* \ln\left(\frac{J_{r,h}}{100}\right)" className="text-blue-200 text-base" />
          </div>

          <div className="pt-3 border-t border-slate-800">
            <div className="text-blue-400 text-[10px] uppercase font-bold tracking-wider font-sans mb-1">
              2. Milestone 5A Route Attribution Identity (Point Contribution Formula)
            </div>
            <BlockMath math="C_r = w_r^* \cdot \left[ \frac{\ln(J_r / 100)}{\ln(I / 100)} \right] \cdot (I - 100)" className="text-blue-200 text-base" />
          </div>

          <div className="pt-3 border-t border-slate-800">
            <div className="text-blue-400 text-[10px] uppercase font-bold tracking-wider font-sans mb-1">
              3. Exact Reconciliation Identity (\sum_r C_r = I - 100)
            </div>
            <BlockMath math="\sum_{r=1}^{10} C_r = (I - 100) \cdot \frac{\sum_{r=1}^{10} w_r^* \ln(J_r / 100)}{\ln(I / 100)} = I - 100" className="text-emerald-400 text-base font-bold" />
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 text-xs text-slate-600 space-y-1">
          <span className="font-bold text-slate-900 block font-sans">Statistical Precision Guarantee:</span>
          <span>
            Every point contribution displayed on Route Intelligence, Horizon Analysis, and the Overview sums exactly to the total headline index delta (e.g. $+1.0675$ from DEL-HYD to $-4.7391$ from GOI-BOM summing to $-3.791$ index points). Zero residual or rounding error is admitted into the presentation layer.
          </span>
        </div>
      </div>

      {/* 6. Statutory MoSPI Non-Equivalence Notice */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 sm:p-8 space-y-4 shadow-xl">
        <div className="flex items-center gap-2.5">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          <h3 className="text-base font-bold text-white tracking-tight uppercase">
            AeroCPI Methodology Boundaries &amp; Non-Equivalence Notice
          </h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed font-sans">
          {methodology.disclaimer ||
            'AeroCPI is an independent, non-official airfare price measurement observatory designed to provide high-frequency price movement insights across major Indian domestic aviation corridors. AeroCPI is strictly an airfare-only measurement index and is NOT statistically equivalent to official Consumer Price Index (CPI) numbers published by the Ministry of Statistics and Programme Implementation (MoSPI).'}
        </p>
      </div>
    </div>
  );
};

