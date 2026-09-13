import React from 'react';
import { RouteDriverItem } from '../types';

interface DriverSectionProps {
  drivers: {
    top_positive_drivers: RouteDriverItem[];
    top_negative_drivers: RouteDriverItem[];
  };
  onSelectRoute: (routeId: string) => void;
}

export const DriverSection: React.FC<DriverSectionProps> = ({ drivers, onSelectRoute }) => {
  const { top_positive_drivers, top_negative_drivers } = drivers;

  // Determine the max absolute contribution to set the zero-axis scale dynamically
  const maxContrib = Math.max(
    ...top_positive_drivers.map((d) => Math.abs(d.point_contribution || 0)),
    ...top_negative_drivers.map((d) => Math.abs(d.point_contribution || 0)),
    4.5
  );

  const totalPositive = top_positive_drivers.reduce((acc, d) => acc + (d.point_contribution || 0), 0);
  const totalNegative = top_negative_drivers.reduce((acc, d) => acc + (d.point_contribution || 0), 0);
  const netSum = totalPositive + totalNegative;

  return (
    <section data-testid="driver-section" aria-label="Route Drivers Attribution" className="bg-white rounded-2xl border border-slate-200/80 shadow-[0_2px_12px_-1px_rgba(15,23,42,0.03)] p-6 sm:p-7 flex flex-col justify-between overflow-hidden">
      {/* Header */}
      <div className="pb-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">WHY DID IT MOVE?</h2>
          <p className="text-xs text-slate-500 mt-1">
            Exact additive point contributions derived from persisted 5A decomposition.
          </p>
        </div>
      </div>

      {/* Screen Reader Only Description */}
      <div className="sr-only">
        Contribution Visualization: Top drivers moving the index.
        {top_negative_drivers.map(d => `Route ${d.route_id} contributed ${d.point_contribution?.toFixed(3)} points. `)}
        {top_positive_drivers.map(d => `Route ${d.route_id} contributed +${d.point_contribution?.toFixed(3)} points. `)}
      </div>

      {/* Diverging Bar Chart Container */}
      <div className="py-6 relative min-h-[300px]" aria-hidden="true">
        {/* Zero Axis Line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-300 z-0"></div>
        <div className="absolute left-1/2 top-0 -translate-x-1/2 bg-white px-2 text-[10px] font-bold text-slate-400 font-mono">
          0.00
        </div>

        <div className="mt-8 space-y-4 relative z-10 w-full">
          {[...top_negative_drivers, ...top_positive_drivers].map((item) => {
            const val = item.point_contribution ?? 0;
            const isNegative = val < 0;
            const absVal = Math.abs(val);
            // 50% width is the max allowed for a bar
            const barWidthPercent = (absVal / maxContrib) * 50;
            const formattedVal = isNegative ? val.toFixed(2) : `+${val.toFixed(2)}`;
            const colorClass = isNegative ? "bg-coral-500" : "bg-emerald-500";

            return (
              <button
                type="button"
                key={item.route_id}
                onClick={() => onSelectRoute(item.route_id)}
                className="w-full relative flex items-center group cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 rounded p-1 hover:bg-slate-50 transition-colors"
              >
                {/* 50% Left Side (Negative Space) */}
                <div className="w-1/2 flex items-center justify-end pr-2 relative h-5">
                  {/* Route Label - Absolutely positioned left, moving inwards */}
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 flex flex-col items-start z-20 pointer-events-none">
                    <span className="font-mono text-slate-900 text-xs font-bold group-hover:text-blue-600 transition-colors">{item.route_id}</span>
                  </div>

                  {/* Negative Bar */}
                  {isNegative && (
                    <div 
                      className={`h-4 ${colorClass} rounded-l-md transition-all group-hover:opacity-80`} 
                      style={{ width: `${barWidthPercent}%` }} 
                    />
                  )}
                  {isNegative && (
                    <span className="absolute -left-12 top-1/2 -translate-y-1/2 text-coral-600 font-bold font-mono text-[10px] whitespace-nowrap">
                      {formattedVal}
                    </span>
                  )}
                </div>

                {/* 50% Right Side (Positive Space) */}
                <div className="w-1/2 flex items-center justify-start pl-2 relative h-5">
                  {/* Positive Bar */}
                  {!isNegative && (
                    <div 
                      className={`h-4 ${colorClass} rounded-r-md transition-all group-hover:opacity-80`} 
                      style={{ width: `${barWidthPercent}%` }} 
                    />
                  )}
                  {!isNegative && (
                    <span className="absolute text-emerald-600 font-bold font-mono text-[10px] whitespace-nowrap ml-1" style={{ left: `calc(${barWidthPercent}% + 4px)` }}>
                      {formattedVal}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
};
