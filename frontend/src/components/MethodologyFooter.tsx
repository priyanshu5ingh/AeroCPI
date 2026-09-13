import React from 'react';
import { AlertCircle } from 'lucide-react';
import { MethodologySummary } from '../types';

interface MethodologyFooterProps {
  methodology: MethodologySummary;
}

export const MethodologyFooter: React.FC<MethodologyFooterProps> = ({ methodology }) => {
  return (
    <footer className="mt-10 border-t border-slate-200/60 pt-6 pb-12 space-y-5">
      <div className="max-w-[1600px] mx-auto space-y-5">
        {/* Core Methodology Version Badges (Quieter & Secondary) */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="bg-slate-50/70 border border-slate-200/60 rounded-xl p-3 flex flex-col gap-0.5">
            <span className="text-[10px] text-slate-400 uppercase font-sans font-semibold">Methodology</span>
            <span className="text-slate-700 font-medium truncate">{methodology.methodology_version}</span>
          </div>

          <div className="bg-slate-50/70 border border-slate-200/60 rounded-xl p-3 flex flex-col gap-0.5">
            <span className="text-[10px] text-slate-400 uppercase font-sans font-semibold">Basket Version</span>
            <span className="text-slate-700 font-medium truncate">{methodology.basket_version}</span>
          </div>

          <div className="bg-slate-50/70 border border-slate-200/60 rounded-xl p-3 flex flex-col gap-0.5">
            <span className="text-[10px] text-slate-400 uppercase font-sans font-semibold">Proxy Weights</span>
            <span className="text-slate-700 font-medium truncate">{methodology.proxy_weight_version}</span>
          </div>

          <div className="bg-slate-50/70 border border-slate-200/60 rounded-xl p-3 flex flex-col gap-0.5">
            <span className="text-[10px] text-slate-400 uppercase font-sans font-semibold">Software Engine</span>
            <span className="text-slate-600 font-medium truncate">{methodology.software_version}</span>
          </div>
        </div>

        {/* Methodology Boundary & CPI Non-Equivalence Disclaimer Box */}
        <div className="bg-amber-50/60 border border-amber-200/80 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-start gap-3.5">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800 font-mono">
              Official Methodological Disclaimer &amp; Boundary Notice
            </h4>
            <p className="text-xs text-amber-900 leading-relaxed font-sans">
              {methodology.disclaimer ||
                'AeroCPI is an independent real-time airfare price index designed to augment CPI and is not statistically equivalent to CPI.'}
            </p>
          </div>
        </div>

        {/* Footer Copyright & Open Standards Note */}
        <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 font-sans gap-3 pt-3 border-t border-slate-100">
          <span>AeroCPI Price Measurement Observatory © 2026. Civil Aviation Economic Benchmarks.</span>
          <div className="flex flex-wrap items-center gap-4 text-[11px] font-medium text-slate-400">
            <span>DGCA Passenger Traffic Weighted Jevons Aggregate</span>
            <span>•</span>
            <span>T+15 Headline Standard</span>
            <span>•</span>
            <span>Deterministic Reproducibility Manifest</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
