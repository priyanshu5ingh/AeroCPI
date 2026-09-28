import React from 'react';
import { Database, TrendingUp, AlertCircle } from 'lucide-react';

export const ProductionEmptyState: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4 space-y-6">
      <div className="w-24 h-24 rounded-full bg-slate-900 flex items-center justify-center border border-slate-800">
        <Database className="w-10 h-10 text-slate-500" />
      </div>
      <div className="space-y-3 max-w-xl">
        <h2 className="text-2xl font-black text-slate-100 tracking-tight">Production Environment Active</h2>
        <p className="text-slate-400 font-sans leading-relaxed">
          The AeroCPI index is currently initializing its longitudinal database. 
          Deep market analysis, historical comparisons, and mathematical audits will become available once sufficient daily observations are collected.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-4 pt-4">
        <div className="px-4 py-3 rounded-2xl bg-slate-900 border border-slate-800 flex items-center gap-3">
          <TrendingUp className="w-5 h-5 text-indigo-400" />
          <div className="text-left">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Next Step</div>
            <div className="text-sm font-medium text-slate-300">Collect 7-day pairs</div>
          </div>
        </div>
        <div className="px-4 py-3 rounded-2xl bg-slate-900 border border-slate-800 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-emerald-400" />
          <div className="text-left">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">System Status</div>
            <div className="text-sm font-medium text-emerald-400">Live & Ready</div>
          </div>
        </div>
      </div>
    </div>
  );
};
