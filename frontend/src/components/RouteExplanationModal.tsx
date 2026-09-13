import React from 'react';
import { X, TrendingUp, TrendingDown, Minus, Info, Calculator } from 'lucide-react';
import { IndexExplanationResponse, RouteContributionExplanation } from '../types';
import { BlockMath } from './MathView';

interface RouteExplanationModalProps {
  routeId: string | null;
  explanation: IndexExplanationResponse | null;
  onClose: () => void;
}

export const RouteExplanationModal: React.FC<RouteExplanationModalProps> = ({
  routeId,
  explanation,
  onClose,
}) => {
  if (!routeId || !explanation) return null;

  // Locate route contribution in headline horizon
  const headlineHorizon = explanation.horizons.find(
    (h) => h.horizon_code === explanation.headline_horizon_code
  ) || explanation.horizons[0];

  const routeContrib: RouteContributionExplanation | undefined = headlineHorizon?.route_contributions.find(
    (r) => r.route_id === routeId
  );

  const missingInfo = headlineHorizon?.missing_routes.find((m) => m.route_id === routeId);

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
      aria-labelledby="route-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200 cursor-pointer"
    >
      <div 
        onClick={(e) => e.stopPropagation()}
        className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative text-slate-900 max-h-[90vh] overflow-y-auto cursor-default"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-xl text-blue-600">
              <Calculator className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 id="route-modal-title" className="text-xl font-bold font-mono text-slate-900">{routeId}</h3>
                <span className="bg-slate-100 text-slate-700 text-xs px-2 py-0.5 rounded font-mono font-medium">
                  {explanation.headline_horizon_code} Headline
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Milestone 5A Transparent Mathematical Route Attribution
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

        {/* Content Body */}
        {routeContrib ? (
          <div className="space-y-5 pt-4">
            {/* Direction & Point Contribution Hero */}
            <div className="bg-slate-50 border border-slate-200/90 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Point Contribution ($C_r$)
                </span>
                <div className="flex items-baseline gap-2 flex-wrap">
                  <span
                    className={`text-3xl font-mono font-extrabold ${
                      routeContrib.direction === 'POSITIVE'
                        ? 'text-emerald-600'
                        : routeContrib.direction === 'NEGATIVE'
                        ? 'text-red-600'
                        : 'text-slate-700'
                    }`}
                  >
                    {routeContrib.point_contribution !== null && routeContrib.point_contribution !== undefined
                      ? `${Number(routeContrib.point_contribution) > 0 ? '+' : ''}${Number(routeContrib.point_contribution).toFixed(4)} pts`
                      : '0.0000 pts'}
                  </span>
                  <span className="text-xs font-mono text-slate-500">
                    to national shift ({explanation.headline_index_value.toFixed(2)} - 100.0)
                  </span>
                </div>
              </div>

              <div
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold flex items-center gap-1.5 border shadow-sm ${
                  routeContrib.direction === 'POSITIVE'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : routeContrib.direction === 'NEGATIVE'
                    ? 'bg-red-50 text-red-700 border-red-200'
                    : 'bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {routeContrib.direction === 'POSITIVE' && <TrendingUp className="w-4 h-4" />}
                {routeContrib.direction === 'NEGATIVE' && <TrendingDown className="w-4 h-4" />}
                {routeContrib.direction === 'NEUTRAL' && <Minus className="w-4 h-4" />}
                <span>{routeContrib.direction} ATTRIBUTION</span>
              </div>
            </div>

            {/* Fare & Relative Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
              <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl">
                <span className="text-slate-500 block font-sans text-[11px] mb-1 font-medium">Base Fare ($P_0$)</span>
                <span className="text-slate-900 font-bold text-sm">₹{routeContrib.base_representative_fare?.toLocaleString()}</span>
                <span className="text-[10px] text-slate-400 block mt-0.5 font-sans">{explanation.reference_date}</span>
              </div>

              <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl">
                <span className="text-slate-500 block font-sans text-[11px] mb-1 font-medium">Current Fare ($P_t$)</span>
                <span className="text-slate-900 font-bold text-sm">₹{routeContrib.current_representative_fare?.toLocaleString()}</span>
                <span className="text-[10px] text-slate-400 block mt-0.5 font-sans">{explanation.calculation_date}</span>
              </div>

              <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl">
                <span className="text-slate-500 block font-sans text-[11px] mb-1 font-medium">Price Relative</span>
                <span className="text-blue-600 font-bold text-sm">{Number(routeContrib.price_relative || 0).toFixed(4)}</span>
                <span className="text-[10px] text-slate-400 block mt-0.5 font-sans">Ratio $P_t / P_0$</span>
              </div>

              <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl">
                <span className="text-slate-500 block font-sans text-[11px] mb-1 font-medium">Route Index ($J_r$)</span>
                <span className="text-blue-600 font-bold text-sm">{Number(routeContrib.route_index_value || 0).toFixed(2)}</span>
                <span className="text-[10px] text-slate-400 block mt-0.5 font-sans">Base = 100.0</span>
              </div>
            </div>

            {/* Weights & Log Contributions */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2 font-mono text-xs">
              <h4 className="font-sans font-bold text-slate-700 text-xs uppercase tracking-wider">
                Weighting &amp; Logarithm Identity Breakdown
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <div className="flex flex-col">
                  <span className="text-slate-500 font-sans text-[11px]">DGCA Basket Weight ($w_r$)</span>
                  <span className="text-slate-800 font-bold">{Number(routeContrib.dgca_basket_weight || 0).toFixed(6)}</span>
                </div>

                <div className="flex flex-col">
                  <span className="text-slate-500 font-sans text-[11px]">Active Renormalized ($w_r^*$)</span>
                  <span className="text-blue-600 font-bold">{Number(routeContrib.active_weight || 0).toFixed(6)}</span>
                </div>

                <div className="flex flex-col">
                  <span className="text-slate-500 font-sans text-[11px]">Log Contribution</span>
                  <span className="text-slate-800 font-bold">{Number(routeContrib.log_contribution || 0).toFixed(6)}</span>
                </div>
              </div>
            </div>

            {/* Mathematical Identity Guardrail */}
            <div className="bg-blue-50/50 border border-blue-200 rounded-xl p-3.5 text-xs text-slate-600 leading-relaxed flex items-start gap-2.5 font-sans">
              <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div className="space-y-2 flex-1">
                <p>
                  <strong>Milestone 5A Route Attribution Identity:</strong> Exact additive log-linear point attribution under Weighted Geometric National Aggregation with Active Weight Renormalization:
                </p>
                <div className="bg-white/90 border border-blue-100 rounded-lg p-2.5 space-y-2">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-mono block mb-0.5">Route Point Contribution Formula:</span>
                    <BlockMath math="C_r = w_r^* \cdot \left[ \frac{\ln(J_r / 100)}{\ln(I / 100)} \right] \cdot (I - 100)" className="text-blue-900 text-sm font-semibold" />
                  </div>
                  <div className="pt-2 border-t border-blue-100/80">
                    <span className="text-[10px] text-slate-500 uppercase font-mono block mb-0.5">Exact Reconciliation Identity:</span>
                    <BlockMath math="\sum_r C_r = I - 100" className="text-emerald-700 text-sm font-bold" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : missingInfo ? (
          <div className="p-6 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-2 mt-4">
            <h4 className="font-bold text-amber-800 flex items-center gap-1.5">
              Missing / Excluded Route Record
            </h4>
            <p className="text-slate-700">Reason: {missingInfo.reason_code}</p>
            <p className="text-slate-500">{missingInfo.description}</p>
          </div>
        ) : (
          <div className="p-6 text-center text-slate-500 text-xs mt-4">
            No detailed contribution record found for route '{routeId}'.
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-xl transition-colors cursor-pointer"
          >
            Close Explanation
          </button>
        </div>
      </div>
    </div>
  );
};
