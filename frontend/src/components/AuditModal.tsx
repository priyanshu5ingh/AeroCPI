import React from 'react';
import { X, FileText, CheckCircle, ShieldCheck, Database, Key, AlertTriangle, Cpu } from 'lucide-react';
import { IndexAuditResponse } from '../types';

interface AuditModalProps {
  isOpen: boolean;
  audit: IndexAuditResponse | null;
  onClose: () => void;
}

export const AuditModal: React.FC<AuditModalProps> = ({ isOpen, audit, onClose }) => {
  if (!isOpen || !audit) return null;

  const {
    run_identity,
    versions,
    population_audit,
    route_audit,
    reproducibility_audit,
    limitations,
  } = audit;

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div 
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="audit-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200 cursor-pointer"
    >
      <div 
        onClick={(e) => e.stopPropagation()}
        className="bg-white border border-slate-200 rounded-2xl max-w-3xl w-full p-6 shadow-2xl relative text-slate-900 max-h-[90vh] overflow-y-auto cursor-default"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 sticky top-0 bg-white z-10">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-xl text-blue-600">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold font-mono text-slate-900">
                  Milestone 5B Measurement Audit
                </h3>
                <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs px-2 py-0.5 rounded font-mono font-medium">
                  {reproducibility_audit.reproducibility_status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Machine-Readable Audit Record &amp; Artifact Reproducibility Audit
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-5 pt-4">
          {/* Section 1: Canonical Run Fingerprint & Reproducibility */}
          <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4 space-y-2.5 font-mono text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-700 font-sans font-bold flex items-center gap-1.5 text-xs">
                <Key className="w-4 h-4 text-blue-600" /> Canonical SHA-256 Calculation Fingerprint
              </span>
              <span className="bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded text-[11px] font-semibold">
                {reproducibility_audit.manifest_present ? 'Manifest Present' : 'No Manifest'}
              </span>
            </div>

            <div className="p-3 bg-white rounded-lg border border-slate-200 text-blue-700 break-all select-all font-bold text-xs">
              {reproducibility_audit.canonical_run_fingerprint}
            </div>

            {reproducibility_audit.manifest_sha256 && (
              <div className="flex items-center justify-between text-[11px] text-slate-500 font-sans">
                <span>Manifest SHA-256:</span>
                <span className="text-slate-700 font-mono truncate max-w-xs">{reproducibility_audit.manifest_sha256}</span>
              </div>
            )}
          </div>

          {/* Section 2: Run Identity & Version Provenance */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Run Identity Box */}
            <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4 space-y-2 text-xs">
              <h4 className="font-bold text-slate-700 uppercase tracking-wider text-[11px] mb-2 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-blue-600" /> Run Identity
              </h4>

              <div className="space-y-1.5 font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Run ID:</span>
                  <span className="text-slate-800">{run_identity.run_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Reference Period:</span>
                  <span className="text-slate-800">{run_identity.reference_period}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Comparison Period:</span>
                  <span className="text-slate-800">{run_identity.comparison_period}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Index Method:</span>
                  <span className="text-blue-700 font-bold">{run_identity.index_method}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Headline Index:</span>
                  <span className="text-slate-900 font-bold">
                    {run_identity.headline_index_value.toFixed(2)} ({run_identity.headline_horizon_code})
                  </span>
                </div>
              </div>
            </div>

            {/* Version Audit Box */}
            <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4 space-y-2 text-xs">
              <h4 className="font-bold text-slate-700 uppercase tracking-wider text-[11px] mb-2 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-emerald-600" /> Version Provenance
              </h4>

              <div className="space-y-1.5 font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Methodology:</span>
                  <span className="text-blue-700 font-bold">{versions.methodology_version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Basket Version:</span>
                  <span className="text-slate-800 font-bold">{versions.route_basket_version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Proxy Weights:</span>
                  <span className="text-emerald-700 font-bold">{versions.proxy_weight_version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Software Version:</span>
                  <span className="text-slate-800">{versions.software_version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Quality Rules:</span>
                  <span className="text-slate-700">{versions.quality_rule_version}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Population & Route Audit */}
          <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4 space-y-3 text-xs font-mono">
            <h4 className="font-sans font-bold text-slate-700 text-xs uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> Observation &amp; Route Population Audit
            </h4>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              <div className="p-3 bg-white rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 block font-sans">Total Observations</span>
                <span className="text-slate-900 font-bold text-sm">
                  {population_audit.total_observations_queried.toLocaleString()}
                </span>
              </div>

              <div className="p-3 bg-white rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 block font-sans">Eligible Observations</span>
                <span className="text-emerald-700 font-bold text-sm">
                  {population_audit.total_eligible_observations.toLocaleString()}
                </span>
              </div>

              <div className="p-3 bg-white rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 block font-sans">Excluded</span>
                <span className="text-slate-700 font-bold text-sm">
                  {population_audit.total_excluded_observations}
                </span>
              </div>

              <div className="p-3 bg-white rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 block font-sans">Basket Routes</span>
                <span className="text-blue-700 font-bold text-sm">
                  {route_audit.total_basket_routes} routes
                </span>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-200">
              <span>Provenance Status:</span>
              <span className="text-slate-800 font-bold font-sans">{population_audit.provenance_status}</span>
            </div>
          </div>

          {/* Section 4: Audit Limitations */}
          {limitations && limitations.length > 0 && (
            <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 space-y-2">
              <h4 className="font-bold text-amber-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-600" /> Known Audit Limitations &amp; Provenance Notes ({limitations.length})
              </h4>
              <ul className="space-y-1.5 text-xs text-amber-950 list-disc list-inside">
                {limitations.map((lim, idx) => (
                  <li key={idx} className="leading-relaxed font-sans">
                    {lim}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-xl transition-colors cursor-pointer"
          >
            Close Audit View
          </button>
        </div>
      </div>
    </div>
  );
};
