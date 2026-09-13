import React from 'react';
import { ArrowDownRight, ArrowUpRight, Minus, Info, Calendar, Compass, GitCommit } from 'lucide-react';
import { DashboardHeadline, DriverSummary } from '../types';
import { AnimatedNumber } from './AnimatedNumber';

interface HeroCardProps {
  headline: DashboardHeadline;
  drivers?: DriverSummary;
  onTraceMeasurement?: () => void;
}

export const HeroCard: React.FC<HeroCardProps> = ({ headline, drivers, onTraceMeasurement }) => {
  const isDown = headline.direction === 'DOWN' || headline.change_from_base < 0;
  const isUp = headline.direction === 'UP' || headline.change_from_base > 0;
  
  const sign = headline.change_from_base > 0 ? '+' : '';
  const formattedChange = `${sign}${headline.change_from_base.toFixed(2)}`;

  const topNeg = drivers?.top_negative_drivers?.[0];
  const topPos = drivers?.top_positive_drivers?.[0];

  return (
    <section className="surface-solid p-7 sm:p-9 relative overflow-hidden">
      {/* Subtle atmospheric gradient corner */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-blue-500/3 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

      <div className="relative z-10 flex flex-col xl:flex-row xl:items-start xl:justify-between gap-8">
        {/* Main Headline Metric Block */}
        <div className="space-y-4 max-w-3xl">
          {/* Metadata Badges */}
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              AeroCPI Headline
            </span>

            <span className="text-xs font-mono font-semibold text-slate-700 bg-slate-100/90 border border-slate-200/60 px-2 py-0.5 rounded">
              {headline.index_name || `AeroCPI_${headline.horizon_code.replace('+', '')}`}
            </span>
            <span className="text-slate-300">·</span>
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              AeroCPI Basket Aggregate
            </span>
          </div>

          {/* Large Headline Figure & Movement Badge */}
          <div className="flex items-baseline gap-4 sm:gap-6 flex-wrap pt-1">
            <h1 className="text-6xl sm:text-7xl font-black tracking-tight text-slate-900 mono-number">
              <AnimatedNumber value={headline.index_value} decimals={2} />
            </h1>

            {/* Movement Callout Badge */}
            <div
              className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-sm font-bold border shadow-xs ${
                isDown
                  ? 'bg-emerald-50/90 text-emerald-700 border-emerald-200/90'
                  : isUp
                  ? 'bg-rose-50/90 text-rose-700 border-rose-200/90'
                  : 'bg-slate-50 text-slate-700 border-slate-200'
              }`}
            >
              {isDown && <ArrowDownRight className="w-4 h-4 text-emerald-600 shrink-0" />}
              {isUp && <ArrowUpRight className="w-4 h-4 text-rose-600 shrink-0" />}
              {!isDown && !isUp && <Minus className="w-4 h-4 text-slate-500 shrink-0" />}
              <span className="font-mono">{formattedChange} index points</span>
              <span className="text-xs font-medium opacity-80">vs baseline</span>
            </div>

            {/* Flagship Feature Trigger: Trace this measurement */}
            {onTraceMeasurement && (
              <button
                type="button"
                onClick={onTraceMeasurement}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50/90 text-blue-700 border border-blue-200/90 text-xs font-bold hover:bg-blue-100/90 transition-all cursor-pointer shadow-xs"
              >
                <GitCommit className="w-3.5 h-3.5 text-blue-600" />
                <span>Trace this measurement →</span>
              </button>
            )}
          </div>

          {/* Dynamic Non-Causal Plain-English Statistical Narrative */}
          <div className="space-y-1.5 pt-1">
            <p className="text-base sm:text-lg text-slate-800 leading-relaxed font-medium">
              Airfare price level is{' '}
              <span className="font-bold text-slate-900">
                {Math.abs(headline.change_from_base).toFixed(2)} points {isDown ? 'below' : 'above'}
              </span>{' '}
              the reference baseline
              {topNeg ? (
                <>
                  , with primary downward relief driven by{' '}
                  <span className="font-mono font-bold text-slate-900">{topNeg.route_id}</span>.
                </>
              ) : (
                '.'
              )}
            </p>
            {topPos && (
              <p className="text-sm text-slate-500 font-normal">
                Primary upward driver:{' '}
                <span className="font-mono font-semibold text-slate-700">
                  {topPos.route_id} ({topPos.point_contribution ? `+${topPos.point_contribution.toFixed(2)}` : ''} index points)
                </span>{' '}
                across the 10-corridor DGCA basket.
              </p>
            )}
          </div>
        </div>

        {/* Micro Information Rail */}
        <div className="xl:border-l xl:border-slate-100 xl:pl-8 flex flex-col justify-center space-y-3.5 min-w-[320px] pt-1 xl:pt-0">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Reference Base & Calculation Window
            </span>
            <div className="flex items-center gap-2 text-xs font-mono font-medium text-slate-700">
              <Calendar className="w-3.5 h-3.5 text-blue-600 shrink-0" />
              <span>Base: {headline.reference_date} (=100.00)</span>
              <span className="text-slate-300">→</span>
              <span>Calc: {headline.calculation_date}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Sampling Specification & Population
            </span>
            <div className="flex items-center gap-2 text-xs text-slate-700 font-medium font-sans">
              <Compass className="w-3.5 h-3.5 text-blue-600 shrink-0" />
              <span>DGCA 10-Route Sovereign Basket • N = 5,332 Observations</span>
            </div>
          </div>

          <div className="pt-2.5 border-t border-slate-100 flex items-start gap-2 text-xs text-slate-500 leading-normal">
            <Info className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
            <span>
              AeroCPI is an independent airfare measurement index designed to augment CPI and is not statistically equivalent to CPI.
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
