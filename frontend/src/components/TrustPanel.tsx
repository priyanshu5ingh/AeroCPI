import React from 'react';
import { ShieldCheck, Info, Activity } from 'lucide-react';
import { DashboardTrustSummary } from '../types';

interface TrustPanelProps {
  trust: DashboardTrustSummary;
}

export const TrustPanel: React.FC<TrustPanelProps> = ({ trust }) => {
  const { trust_status, trust_score } = trust;

  const getStatusBadge = () => {
    switch (trust_status) {
      case 'HIGH':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'MODERATE':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'DEGRADED':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'LOW':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'UNEVALUATED':
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="surface-solid p-6 flex flex-col justify-between">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">TRUST</h3>
          </div>
          <span className="text-[11px] font-mono text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
            Diagnostic Only
          </span>
        </div>

        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Measurement Trust Evaluation
        </p>

        {/* Status Callout Box */}
        <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">Evaluation Status</span>
            <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold border ${getStatusBadge()}`}>
              {trust_status}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">Confidence Score</span>
            <span className="font-mono text-xs font-bold text-slate-700">
              {trust_score !== null ? `${(trust_score * 100).toFixed(0)} / 100` : '—'}
            </span>
          </div>
        </div>

        {/* Diagnostic Explanation Notice */}
        <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-3 text-xs text-slate-600 leading-relaxed flex items-start gap-2">
          <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <span>
            {trust_status === 'UNEVALUATED'
              ? 'Trust evaluation not attached to this index run.'
              : `Diagnostic evaluation computed with status: ${trust_status}`}
          </span>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <span className="flex items-center gap-1">
          <Activity className="w-3.5 h-3.5 text-blue-500" /> Statistical guardrails active
        </span>
        <span>Diagnostic guard</span>
      </div>
    </div>
  );
};
