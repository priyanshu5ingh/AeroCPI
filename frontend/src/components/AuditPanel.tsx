import React from 'react';
import { FileText, CheckCircle, ExternalLink, Shield, AlertTriangle } from 'lucide-react';
import { DashboardAuditSummary } from '../types';

interface AuditPanelProps {
  audit: DashboardAuditSummary;
  onOpenAudit: () => void;
}

export const AuditPanel: React.FC<AuditPanelProps> = ({ audit, onOpenAudit }) => {
  const fingerprintTruncated = audit.canonical_run_fingerprint
    ? `${audit.canonical_run_fingerprint.substring(0, 8)}...${audit.canonical_run_fingerprint.substring(
        audit.canonical_run_fingerprint.length - 8
      )}`
    : '—';

  return (
    <button
      type="button"
      data-testid="audit-panel-card"
      onClick={onOpenAudit}
      className="w-full text-left surface-solid p-6 group cursor-pointer hover:border-blue-400  flex flex-col justify-between transition-all duration-200"
    >
      <div className="w-full space-y-3">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 w-full">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600 group-hover:text-blue-700 transition-colors" />
            <h3 className="text-sm font-bold text-slate-900 group-hover:text-blue-700 transition-colors tracking-tight">
              AUDIT & EVIDENCE
            </h3>
          </div>
          <div className="flex items-center gap-1 text-xs text-blue-600 font-medium group-hover:translate-x-0.5 transition-transform">
            <span>Inspect 5B</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </div>
        </div>

        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Measurement Audit & Reproducibility
        </p>

        {/* Audit Details */}
        <div className="space-y-2 font-mono text-xs w-full">
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-slate-500 font-sans">Reproducibility</span>
            <span className="font-bold text-emerald-700 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> {audit.reproducibility_status}
            </span>
          </div>

          <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-slate-500 font-sans">Manifest</span>
            <span className="font-bold text-emerald-700 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> {audit.manifest_present ? 'Present' : 'Missing'}
            </span>
          </div>

          <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-slate-500 font-sans">Fingerprint</span>
            <span className="text-slate-700 text-[11px] font-mono">{fingerprintTruncated}</span>
          </div>

          <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-slate-500 font-sans">Known Limitations</span>
            <span className="text-amber-700 font-bold flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> {audit.limitations.length} items
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 w-full">
        <span className="flex items-center gap-1 text-slate-600 font-sans">
          <Shield className="w-3.5 h-3.5 text-blue-600" /> Click to open 5B Audit View
        </span>
        <span className="font-mono text-blue-600 font-semibold group-hover:underline">Open →</span>
      </div>
    </button>
  );
};
