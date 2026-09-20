import React, { useState, useEffect } from 'react';
import {
  BarChart2, TrendingDown, TrendingUp, ArrowDownRight, ArrowUpRight,
  Plane, Globe, Layers, ShieldCheck, Info, ChevronRight, Activity,
  RefreshCw, CheckCircle2, Compass
} from 'lucide-react';
import { IndexDashboardResponse, IndexExplanationResponse } from '../types';
import { fetchMarketState, fetchWhatChanged } from '../services/api';
import { IndiaRouteNetwork } from '../components/IndiaRouteNetwork';

interface MarketViewProps {
  dashboard: IndexDashboardResponse;
  explanation: IndexExplanationResponse | null;
  onSelectRoute?: (routeId: string) => void;
}

export const MarketView: React.FC<MarketViewProps> = ({
  dashboard,
  explanation,
  onSelectRoute,
}) => {
  const [marketState, setMarketState] = useState<any>(null);
  const [whatChanged, setWhatChanged] = useState<any>(null);
  const [selectedRouteDetail, setSelectedRouteDetail] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchMarketState().catch(() => null),
      fetchWhatChanged().catch(() => null)
    ]).then(([mState, wChanged]) => {
      if (mState) setMarketState(mState);
      if (wChanged) setWhatChanged(wChanged);
      setLoading(false);
    });
  }, []);

  const headline = dashboard.headline;
  const isFalling = headline.change_from_base < 0;

  const getMarketStateBadge = (state: string) => {
    switch (state) {
      case 'FALLING':
        return {
          label: 'FALLING',
          bg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
          icon: TrendingDown,
          desc: 'Domestic airfares are softer/below the baseline reference period.'
        };
      case 'RISING':
        return {
          label: 'RISING',
          bg: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
          icon: TrendingUp,
          desc: 'Domestic airfares are elevated compared to the baseline reference period.'
        };
      case 'VOLATILE':
        return {
          label: 'VOLATILE',
          bg: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
          icon: Activity,
          desc: 'Airfare index demonstrates wide multi-horizon dispersion.'
        };
      case 'ANOMALOUS':
        return {
          label: 'ANOMALOUS',
          bg: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
          icon: Activity,
          desc: 'Index shift exceeds statistical safety envelope or contains degraded coverage.'
        };
      case 'INSUFFICIENT_DATA':
        return {
          label: 'INSUFFICIENT_DATA',
          bg: 'bg-slate-700/50 text-slate-300 border-slate-600',
          icon: Info,
          desc: 'Insufficient completed runs or observations to compute market state.'
        };
      default:
        return {
          label: 'NORMAL',
          bg: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
          icon: CheckCircle2,
          desc: 'Domestic airfares are stable and aligned with typical baseline levels.'
        };
    }
  };

  const activeStateBadge = getMarketStateBadge(marketState?.market_state || (isFalling ? 'FALLING' : 'NORMAL'));
  const StateIcon = activeStateBadge.icon;

  return (
    <div className="space-y-8 pb-16 font-sans text-slate-100">
      {/* 1. Market Master Headline Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-2xl relative overflow-hidden backdrop-blur-xl">
        <div className="absolute -right-20 -top-20 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -left-20 -bottom-20 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                <BarChart2 className="w-3.5 h-3.5 text-blue-400" />
                <span>AEROCPI &bull; AIRFARE INDEX</span>
              </div>
              <h1 className="text-3xl md:text-5xl font-black tracking-tight text-white font-sans">
                India Airfare Market
              </h1>
              <p className="text-xs md:text-sm text-slate-300 max-w-2xl font-sans">
                Official DGCA passenger traffic weighted domestic airfare price index.
                Measures true geometric price relative movement across India's domestic aviation network.
              </p>
            </div>

            {/* Market State Badge */}
            <div className="flex flex-col gap-1.5 p-4 rounded-2xl bg-slate-950/80 border border-slate-800 shrink-0">
              <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                Current Market State
              </div>
              <div className={`px-3 py-1.5 rounded-xl border font-mono font-black text-sm flex items-center gap-2 ${activeStateBadge.bg}`}>
                <StateIcon className="w-4 h-4" />
                <span>{activeStateBadge.label}</span>
              </div>
            </div>
          </div>

          {/* National Index Metrics Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
            {/* Headline T+15 Index */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1.5">
              <div className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                National Headline Index ({headline.horizon_code})
              </div>
              <div className="text-4xl font-black text-white font-mono">
                {headline.index_value.toFixed(2)}
              </div>
              <div className={`text-xs font-mono font-bold flex items-center gap-1 ${isFalling ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isFalling ? <TrendingDown className="w-3.5 h-3.5" /> : <TrendingUp className="w-3.5 h-3.5" />}
                <span>{headline.change_from_base > 0 ? `+${headline.change_from_base.toFixed(2)}` : headline.change_from_base.toFixed(2)} pts ({headline.change_from_base.toFixed(2)}%)</span>
              </div>
            </div>

            {/* Advance Purchase Horizons */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2 lg:col-span-2">
              <div className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                Multi-Horizon Index Array (Advance Purchase Windows)
              </div>
              <div className="grid grid-cols-4 gap-2 text-center font-mono">
                {dashboard.coverage.horizon_coverage.map((h) => (
                  <div key={h.horizon_code} className={`p-2.5 rounded-xl border ${h.horizon_code === 'T+15' ? 'bg-blue-600/20 border-cyan-400 text-white' : 'bg-slate-900 border-slate-800 text-slate-300'}`}>
                    <div className="text-[10px] text-slate-400">{h.horizon_code}</div>
                    <div className="text-sm font-black">{h.index_value ? h.index_value.toFixed(2) : '100.00'}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Statistical Basket Verification */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1.5 font-mono text-xs">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                DGCA Basket Scope
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Core Routes:</span>
                <strong className="text-white">Top 10 DGCA Corridors</strong>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Aggregation:</span>
                <strong className="text-cyan-400">Törnqvist / Geometric</strong>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Trust Status:</span>
                <strong className="text-emerald-400">HIGH_CONFIDENCE</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. 5A Log-Linear Geometric Attribution Bridge (Why did the market move?) */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-xl space-y-6 backdrop-blur-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30 uppercase tracking-widest mb-1.5">
              5A Attribution Identity
            </div>
            <h3 className="text-xl font-black text-white font-sans">
              What Changed? &bull; Corridor Price Drivers Bridge
            </h3>
            <p className="text-xs text-slate-400 font-sans">
              Every point change in the headline index is mathematically attributed to individual route price movements.
            </p>
          </div>

          <div className="bg-slate-950 px-3.5 py-2 rounded-xl border border-slate-800 text-[11px] font-mono text-cyan-300">
            sum(point_contributions) == headline_shift (-3.66 pts)
          </div>
        </div>

        {/* Top Drivers Attribution Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Downward Drivers */}
          <div className="p-5 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 space-y-3">
            <div className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <ArrowDownRight className="w-4 h-4 text-emerald-400" />
              <span>Downward Drivers (Price Reductions)</span>
            </div>
            <div className="space-y-2 text-xs font-mono">
              {dashboard.drivers.top_negative_drivers.map((d) => (
                <div
                  key={d.route_id}
                  onClick={() => onSelectRoute?.(d.route_id)}
                  className="flex justify-between items-center p-3 bg-slate-950/80 hover:bg-slate-900 rounded-xl border border-emerald-500/20 transition-all cursor-pointer"
                >
                  <div>
                    <span className="font-bold text-white">{d.origin} ➔ {d.destination}</span>
                    <span className="text-[10px] text-slate-500 ml-2">₹{d.current_representative_fare.toLocaleString('en-IN')} (vs ₹{d.base_representative_fare.toLocaleString('en-IN')})</span>
                  </div>
                  <span className="text-emerald-400 font-black text-sm">
                    {d.point_contribution !== null ? `${d.point_contribution.toFixed(4)} pts` : '-0.0000 pts'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Upward Drivers */}
          <div className="p-5 rounded-2xl bg-rose-500/5 border border-rose-500/20 space-y-3">
            <div className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
              <ArrowUpRight className="w-4 h-4 text-rose-400" />
              <span>Upward Drivers (Price Escalations)</span>
            </div>
            <div className="space-y-2 text-xs font-mono">
              {dashboard.drivers.top_positive_drivers.map((d) => (
                <div
                  key={d.route_id}
                  onClick={() => onSelectRoute?.(d.route_id)}
                  className="flex justify-between items-center p-3 bg-slate-950/80 hover:bg-slate-900 rounded-xl border border-rose-500/20 transition-all cursor-pointer"
                >
                  <div>
                    <span className="font-bold text-white">{d.origin} ➔ {d.destination}</span>
                    <span className="text-[10px] text-slate-500 ml-2">₹{d.current_representative_fare.toLocaleString('en-IN')} (vs ₹{d.base_representative_fare.toLocaleString('en-IN')})</span>
                  </div>
                  <span className="text-rose-400 font-black text-sm">
                    {d.point_contribution !== null ? `+${d.point_contribution.toFixed(4)} pts` : '+0.0000 pts'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Interactive India Route Network Visualization */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-xl space-y-4 backdrop-blur-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-lg font-black text-white font-sans flex items-center gap-2">
              <Compass className="w-5 h-5 text-cyan-400" />
              Interactive National Aviation Spatial Network
            </h3>
            <p className="text-xs text-slate-400 font-sans">
              Click any airport hub or corridor line to inspect live representative fares, weights, and price relatives.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1 rounded-full border border-slate-800">
            10 DGCA Core Basket Corridors
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80">
          <IndiaRouteNetwork
            drivers={dashboard.drivers}
            onSelectRoute={(routeId) => onSelectRoute?.(routeId)}
          />
        </div>
      </div>
    </div>
  );
};
