import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { drawerVariants, drawerBackdropVariants, traceContainerVariants, traceNodeVariants } from '../lib/motion';
import { 
  ShieldCheck, Lock, FileCode, CheckCircle2, AlertCircle, ArrowRight, 
  Database, ChevronRight, Activity, GitCommit, Search, ListFilter, 
  SlidersHorizontal, Hash, LockKeyhole, AlertTriangle, Layers, Info, X 
} from 'lucide-react';
import { 
  IndexDashboardResponse, IndexAuditResponse, IndexExplanationResponse, 
  MeasurementTraceResponse 
} from '../types';
import { fetchMeasurementTrace } from '../services/api';
import { PlatformTab } from '../components/Header';

interface AuditEvidencePageProps {
  dashboard: IndexDashboardResponse;
  audit: IndexAuditResponse;
  explanation: IndexExplanationResponse;
  onOpenAuditModal: () => void;
  onSelectTab: (tab: PlatformTab) => void;
}

type TraceNodeId = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
type NodeCategory = 'MEASUREMENT ARTIFACT' | 'MATHEMATICAL TRANSFORMATION' | 'AUDIT METADATA';

interface TraceNodeDef {
  id: TraceNodeId;
  title: string;
  category: NodeCategory;
  purpose: string;
}

const TRACE_NODES: TraceNodeDef[] = [
  { id: 1, title: 'INDEX RUN', category: 'MEASUREMENT ARTIFACT', purpose: 'Primary execution artifact containing core headline identity and baseline anchoring.' },
  { id: 2, title: 'CONFIGURATION', category: 'AUDIT METADATA', purpose: 'Deterministic snapshot of methodology, parameters, and active basket configuration.' },
  { id: 3, title: 'HORIZONS', category: 'MATHEMATICAL TRANSFORMATION', purpose: 'Calculation of the forward booking curve term structure relative to calculation date.' },
  { id: 4, title: 'ROUTES', category: 'MATHEMATICAL TRANSFORMATION', purpose: 'Log-linear attribution and weighting of individual corridor contributions to the national index.' },
  { id: 5, title: 'REPRESENTATIVE FARES', category: 'MEASUREMENT ARTIFACT', purpose: 'Persisted single-value median fares for both reference baseline and current calculation.' },
  { id: 6, title: 'OBSERVATIONS', category: 'MEASUREMENT ARTIFACT', purpose: 'Raw evidence ledger metadata detailing queried, eligible, and rejected market quotes.' },
  { id: 7, title: 'QUALITY', category: 'AUDIT METADATA', purpose: 'Diagnostic completeness and Trust Engine evaluation states for the active run.' },
  { id: 8, title: 'EXPLANATION', category: 'MATHEMATICAL TRANSFORMATION', purpose: 'Calculated attribution of price movement by routing corridor.' },
  { id: 9, title: 'SHA-256 FINGERPRINT', category: 'AUDIT METADATA', purpose: 'Cryptographic sealing hash linking the canonical run artifact and its execution manifest.' }
];

export const AuditEvidencePage: React.FC<AuditEvidencePageProps> = ({ 
  dashboard, audit, explanation, onOpenAuditModal, onSelectTab 
}) => {
  const [trace, setTrace] = useState<MeasurementTraceResponse | null>(null);
  const [loadingTrace, setLoadingTrace] = useState(true);
  const [selectedNode, setSelectedNode] = useState<TraceNodeId | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoadingTrace(true);
    fetchMeasurementTrace(dashboard.dashboard_scope.run_id)
      .then(res => { if(mounted) setTrace(res); })
      .catch(err => console.error(err))
      .finally(() => { if(mounted) setLoadingTrace(false); });
    return () => { mounted = false; };
  }, [dashboard.dashboard_scope.run_id]);

  const runId = dashboard.dashboard_scope.run_id;
  const headline = dashboard.headline.index_value;
  const baseDate = dashboard.dashboard_scope.reference_date;
  const calcDate = dashboard.dashboard_scope.calculation_date;

  
  const headlineExplanation = explanation.horizons.find(h => h.is_headline);
  const routeContributions = headlineExplanation?.route_contributions || [];
  const positiveContributors = routeContributions.filter(c => c.direction === 'POSITIVE').sort((a,b) => (b.point_contribution || 0) - (a.point_contribution || 0));
  const negativeContributors = routeContributions.filter(c => c.direction === 'NEGATIVE').sort((a,b) => (a.point_contribution || 0) - (b.point_contribution || 0));

  const renderNodeDetails = (nodeId: TraceNodeId) => {
    if (!trace) return null;
    switch (nodeId) {
      case 1:
        return (
          <div className="space-y-4">
            <div><p className="text-xs text-slate-500 font-bold uppercase">Run ID</p><p className="font-mono text-xs text-slate-800">{trace.index_run.run_id}</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Headline Index</p><p className="font-mono text-xs text-slate-800">{trace.index_run.headline_index_value.toFixed(3)} ({trace.index_run.headline_horizon_code})</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Dates</p><p className="font-mono text-xs text-slate-800">Ref: {trace.index_run.reference_date} | Calc: {trace.index_run.calculation_date}</p></div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-4">
            <div><p className="text-xs text-slate-500 font-bold uppercase">Configuration Version</p><p className="font-mono text-xs text-slate-800">{trace.configuration.configuration_version}</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Basket / Aggregation</p><p className="font-mono text-xs text-slate-800">{trace.configuration.basket_version} / {trace.configuration.aggregation_version}</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Fingerprint</p><p className="font-mono text-[10px] text-slate-800 break-all">{trace.configuration.configuration_fingerprint}</p></div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-3">
            {trace.horizons.map(h => (
              <div key={h.horizon_code} className="flex justify-between items-center text-xs font-mono">
                <span className="font-bold">{h.horizon_code}</span>
                <span className="text-slate-600">{h.index_value.toFixed(3)} ({h.active_routes_count} routes)</span>
              </div>
            ))}
          </div>
        );
      case 4:
        return (
          <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
            {trace.routes.map(r => (
              <div key={r.route_id} className="flex justify-between items-center text-[10px] font-mono border-b border-slate-100 pb-1">
                <span className="font-bold">{r.route_id}</span>
                <span className="text-slate-600">Idx: {r.route_index_value.toFixed(1)} | Wgt: {r.dgca_weight.toFixed(4)}</span>
              </div>
            ))}
          </div>
        );
      case 5:
        return (
          <div className="space-y-4">
            <div className="text-xs text-slate-500 italic">Only route-level persisted medians are stored, not raw quotes.</div>
            <div className="text-[10px] font-mono">See Route Intelligence for specific Base and Current fares.</div>
            <button onClick={() => onSelectTab('routes')} className="text-xs text-blue-600 font-bold hover:underline flex items-center gap-1">
              Inspect Route Fares <ArrowRight className="w-3 h-3"/>
            </button>
          </div>
        );
      case 6:
        return (
          <div className="space-y-4">
            <div><p className="text-xs text-slate-500 font-bold uppercase">Total Queried</p><p className="font-mono text-xs text-slate-800">{trace.observation_summary.total_observations_queried ?? 'NOT PERSISTED'}</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Eligible Observations</p><p className="font-mono text-xs text-slate-800">{trace.observation_summary.eligible_observations ?? 'NOT PERSISTED'}</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Rejection Rate</p><p className="font-mono text-xs text-slate-800">{trace.observation_summary.rejection_rate_pct !== null ? `${(trace.observation_summary.rejection_rate_pct * 100).toFixed(1)}%` : 'NOT PERSISTED'}</p></div>
          </div>
        );
      case 7:
        return (
          <div className="space-y-4">
            <div><p className="text-xs text-slate-500 font-bold uppercase">Completeness</p><p className="font-mono text-xs text-slate-800">{(trace.quality_summary.completeness_pct * 100).toFixed(1)}%</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Fare Integrity</p><p className="font-mono text-xs text-slate-800">{(trace.quality_summary.fare_integrity_pct * 100).toFixed(1)}%</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Rule Version</p><p className="font-mono text-xs text-slate-800">{trace.quality_summary.rule_version}</p></div>
          </div>
        );
      case 8:
        return (
          <div className="space-y-4">
            <div><p className="text-xs text-slate-500 font-bold uppercase">Top Positive Contributor</p><p className="font-mono text-xs text-slate-800">{trace.explanation_summary.top_positive_driver} (+{trace.explanation_summary.top_positive_points.toFixed(4)})</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Top Negative Contributor</p><p className="font-mono text-xs text-slate-800">{trace.explanation_summary.top_negative_driver} ({trace.explanation_summary.top_negative_points.toFixed(4)})</p></div>
            <button onClick={() => onSelectTab('routes')} className="text-xs text-blue-600 font-bold hover:underline flex items-center gap-1">View Explanation <ArrowRight className="w-3 h-3"/></button>
          </div>
        );
      case 9:
        return (
          <div className="space-y-4">
            <div><p className="text-xs text-slate-500 font-bold uppercase">Canonical Fingerprint</p><p className="font-mono text-[10px] text-slate-800 break-all">{trace.canonical_run_fingerprint}</p></div>
            <div><p className="text-xs text-slate-500 font-bold uppercase">Manifest SHA-256</p><p className="font-mono text-[10px] text-slate-800 break-all">{trace.manifest_sha256 || 'NOT PERSISTED'}</p></div>
            <div className="text-[10px] text-slate-500 italic mt-2">Canonical fingerprint and manifest hash are semantically distinct persisted artifacts.</div>
          </div>
        );
      default: return null;
    }
  };

  return (
    <div className="surface-solid divide-y divide-slate-100 pb-8">
      {/* 2. Page Hero */}
      <div className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight font-sans">Audit & Measurement Trace</h1>
            <p className="text-slate-500 font-medium">End-to-End Measurement Provenance</p>
            <p className="text-sm text-slate-700 mt-2 font-bold">"How was AeroCPI Headline {headline.toFixed(3)} produced?"</p>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 space-y-1">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">AeroCPI Headline</p>
              <p className="text-2xl font-bold font-mono text-slate-900">{headline.toFixed(3)}</p>
              <p className="text-[10px] font-mono text-slate-500">T+15 | Base: {baseDate}</p>
            </div>
            <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 space-y-1">
              <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">Audit Status</p>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600"/>
                <p className="text-xs font-bold font-mono text-emerald-800">{audit.reproducibility_audit.reproducibility_status}</p>
              </div>
              <p className="text-[10px] font-sans text-emerald-700/80 leading-tight pt-1">Artifact reproducibility does NOT mean a full raw-input rerun is currently guaranteed.</p>
            </div>
          </div>
        </div>
      </div>

      <div>
        {/* 3. Signature Visual - 9 Stage Measurement Trace */}
        <div className="w-full bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 font-sans">Measurement Trace Architecture</h2>
              <p className="text-xs text-slate-500 font-medium">Select a node to inspect provenance artifacts.</p>
            </div>
            {/* Visual Legend */}
            <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-wider flex-wrap">
              <div className="flex items-center gap-1.5 text-blue-600"><Database className="w-3 h-3"/> Artifact</div>
              <div className="flex items-center gap-1.5 text-emerald-600"><Activity className="w-3 h-3"/> Math</div>
              <div className="flex items-center gap-1.5 text-slate-500"><Search className="w-3 h-3"/> Metadata</div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute left-4 top-4 bottom-4 w-0.5 bg-slate-100"></div>
            <div className="space-y-4 relative z-10">
              {TRACE_NODES.map((node) => {
                const isSelected = selectedNode === node.id;
                let Icon = Database;
                let colorClass = "text-blue-600";
                let bgClass = "bg-blue-50";
                let borderClass = "border-blue-200";
                
                if (node.category === 'MATHEMATICAL TRANSFORMATION') {
                  Icon = Activity; colorClass = "text-emerald-600"; bgClass = "bg-emerald-50"; borderClass = "border-emerald-200";
                } else if (node.category === 'AUDIT METADATA') {
                  Icon = Search; colorClass = "text-slate-600"; bgClass = "bg-slate-50"; borderClass = "border-slate-200";
                }

                return (
                  <div key={node.id} 
                    onClick={() => setSelectedNode(node.id)}
                    className={`flex items-start gap-4 p-3 rounded-xl cursor-pointer transition-all duration-300 ${isSelected ? "bg-slate-50 border border-slate-200 shadow-sm translate-x-1" : "hover:bg-slate-50/50 border border-transparent"}`}
                  >
                    <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center border ${bgClass} ${borderClass} ${colorClass}`}>
                      <Icon className="w-4 h-4"/>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono font-bold text-slate-400">0{node.id}</span>
                          <h3 className="text-sm font-bold text-slate-900">{node.title}</h3>
                        </div>
                        {isSelected && <ChevronRight className="w-4 h-4 text-slate-400"/>}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">{node.purpose}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* 6. True Overlay Inspection Drawer */}
        <AnimatePresence>
          {selectedNode && (
            <>
              {/* Backdrop */}
              <motion.div
                variants={drawerBackdropVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                onClick={() => setSelectedNode(null)}
                className="fixed inset-0 bg-slate-900 z-40"
              />
              {/* Drawer Surface */}
              <motion.div
                variants={drawerVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-white/95 backdrop-blur-xl border-l border-slate-200 shadow-[0_0_40px_rgba(15,23,42,0.1)] flex flex-col justify-between overflow-y-auto"
              >
                {(() => {
                  const node = TRACE_NODES.find(n => n.id === selectedNode)!;
                  return (
                    <div className="flex flex-col h-full">
                <div className="p-4 sm:p-6 border-b border-slate-100 bg-slate-50/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">STAGE 0{node.id}</span>
                    <button onClick={() => setSelectedNode(null)} className="text-slate-400 hover:text-slate-600"><X className="w-4 h-4"/></button>
                  </div>
                  <h3 className="text-base font-bold text-slate-900">{node.title}</h3>
                  <p className="text-xs text-slate-500 mt-1">{node.category}</p>
                </div>
                <div className="p-4 sm:p-6 flex-1 overflow-y-auto">
                  {loadingTrace ? (
                    <div className="animate-pulse space-y-4"><div className="h-4 bg-slate-200 rounded w-3/4"></div><div className="h-16 bg-slate-100 rounded"></div></div>
                  ) : (
                    renderNodeDetails(selectedNode)
                  )}
                </div>
                <div className="p-4 border-t border-slate-100 bg-slate-50/50">
                  <p className="text-[10px] text-slate-400 font-mono">All data rendered from frozen persistence layer. Zero client-side computation.</p>
                </div>
              </div>
                  );
                })()}
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>

      {/* 7. Headline Reconciliation */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-900 font-sans">Headline Reconciliation</h2>
          <button onClick={() => onSelectTab('routes')} className="text-xs font-bold text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1">
            View Full Explanation <ArrowRight className="w-3 h-3"/>
          </button>
        </div>
        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-6">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase">AeroCPI Headline</p>
              <p className="text-3xl font-bold font-mono text-slate-900">{explanation.headline_index_value.toFixed(3)}</p>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase">Reference Baseline</p>
              <p className="text-xl font-bold font-mono text-slate-600">100.000</p>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase">Total Change</p>
              <p className={`text-xl font-bold font-mono ${explanation.headline_index_value < 100 ? 'text-coral-600' : 'text-emerald-600'}`}>
                {explanation.headline_index_value < 100 ? '' : '+'}{(explanation.headline_index_value - 100).toFixed(3)} pts
              </p>
            </div>
          </div>
          <div className="col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-8">
            <div className="space-y-3">
              <p className="text-xs font-bold text-emerald-600 uppercase border-b border-slate-100 pb-2">Largest Positive Contributions</p>
              {positiveContributors.slice(0,3).map(c => (
                <div key={c.route_id} className="flex justify-between items-center text-sm font-mono">
                  <span className="font-bold text-slate-700">{c.route_id}</span>
                  <span className="text-emerald-600">+{Number(c.point_contribution || 0).toFixed(4)}</span>
                </div>
              ))}
            </div>
            <div className="space-y-3">
              <p className="text-xs font-bold text-coral-600 uppercase border-b border-slate-100 pb-2">Largest Negative Contributions</p>
              {negativeContributors.slice(0,3).map(c => (
                <div key={c.route_id} className="flex justify-between items-center text-sm font-mono">
                  <span className="font-bold text-slate-700">{c.route_id}</span>
                  <span className="text-coral-600">{Number(c.point_contribution || 0).toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 8. Reproducibility Panel */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden p-6">
        <div className="flex items-center gap-3 mb-4">
          <FileCode className="w-5 h-5 text-slate-700" />
          <h2 className="text-lg font-bold text-slate-900 font-sans">Reproducibility</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="space-y-1">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Artifact Reproducible</p>
            <p className="text-sm font-bold font-mono text-emerald-700">YES</p>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Raw Input Artifacts Available</p>
            <p className="text-sm font-bold font-mono text-slate-700">{audit.reproducibility_audit.raw_input_artifacts_available ? "YES" : "NO"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Full Rerun Reproducibility</p>
            <p className="text-sm font-bold font-mono text-slate-700">{audit.reproducibility_audit.reproducibility_status}</p>
          </div>
        </div>
        <div className="mt-4 p-4 bg-amber-50 border border-amber-200/60 rounded-xl flex gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
          <p className="text-xs text-amber-800 font-sans leading-relaxed">
            <strong>Important:</strong> Artifact reproducibility means that all calculations from the ingested data points to the final index value are cryptographically verified and math-checkable. It does <em>not</em> imply that a complete rerun from original raw HTML web scrape inputs is currently guaranteed or available.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 9. Audit Summary */}
        <div className="bg-slate-900 rounded-2xl p-6 text-slate-300 space-y-4 shadow-md">
          <div className="flex items-center gap-2 mb-2">
            <Lock className="w-5 h-5 text-slate-400"/>
            <h2 className="text-lg font-bold text-white font-sans">Measurement Audit Summary</h2>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs font-mono">
            <div className="text-slate-500">Run Identity</div>
            <div className="text-white text-right break-all">{audit.run_identity.run_id}</div>
            
            <div className="text-slate-500">Config / Basket</div>
            <div className="text-white text-right break-all">{audit.versions.methodology_version} / {audit.versions.route_basket_version}</div>
            
            <div className="text-slate-500">Manifest Status</div>
            <div className="text-white text-right">{audit.reproducibility_audit.manifest_present ? "PRESENT" : "MISSING"}</div>
            
            <div className="text-slate-500">Population Trace</div>
            <div className="text-white text-right">{audit.population_audit.provenance_status}</div>
            
            <div className="text-slate-500">Trust Engine Status</div>
            <div className="text-white text-right">{audit.trust_audit.trust_evaluation_status}</div>
          </div>
          <button onClick={onOpenAuditModal} className="w-full py-2.5 mt-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-bold transition-colors border border-slate-700">
            View Complete Audit JSON
          </button>
        </div>
        
        {/* Helper Context Links */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-4 flex flex-col justify-between">
          <h2 className="text-sm font-bold text-slate-900 uppercase font-sans mb-2">Cross-Module Verification Links</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button onClick={() => onSelectTab('overview')} className="text-left px-3 py-2 text-xs font-bold text-slate-600 bg-slate-50 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-colors border border-transparent hover:border-blue-100 flex justify-between items-center">View Golden Overview <ArrowRight className="w-3 h-3"/></button>
            <button onClick={() => onSelectTab('live-market')} className="text-left px-3 py-2 text-xs font-bold text-slate-600 bg-slate-50 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-colors border border-transparent hover:border-blue-100 flex justify-between items-center">Inspect Evidence <ArrowRight className="w-3 h-3"/></button>
            <button onClick={() => onSelectTab('routes')} className="text-left px-3 py-2 text-xs font-bold text-slate-600 bg-slate-50 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-colors border border-transparent hover:border-blue-100 flex justify-between items-center">Inspect Routes & Explanations <ArrowRight className="w-3 h-3"/></button>
            <button onClick={() => onSelectTab('data-quality')} className="text-left px-3 py-2 text-xs font-bold text-slate-600 bg-slate-50 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-colors border border-transparent hover:border-blue-100 flex justify-between items-center">View Methodology Studio <ArrowRight className="w-3 h-3"/></button>
            <button onClick={() => onSelectTab('validation')} className="text-left px-3 py-2 text-xs font-bold text-slate-600 bg-slate-50 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-colors border border-transparent hover:border-blue-100 flex justify-between items-center col-span-1 sm:col-span-2">Validation Lab <ArrowRight className="w-3 h-3"/></button>
          </div>
        </div>
      </div>
    </div>
  );
};
