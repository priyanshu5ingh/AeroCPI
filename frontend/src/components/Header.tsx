import React, { useState } from 'react';
import {
  Plane, Sparkles, BarChart2, ShieldCheck, Database, Menu, X, Check,
  ChevronDown, ExternalLink, Activity
} from 'lucide-react';
import { DashboardScope, SimpleIndexRun } from '../types';

export type PlatformTab =
  | 'guide'
  | 'market'
  | 'proof'
  | 'overview'
  | 'aeroguide'
  | 'live-market'
  | 'routes'
  | 'horizon'
  | 'methodology'
  | 'data-quality'
  | 'validation'
  | 'audit';

interface HeaderProps {
  scope: DashboardScope;
  runs: SimpleIndexRun[];
  onSelectRun: (runId: string) => void;
  activeTab?: PlatformTab;
  onSelectTab?: (tab: PlatformTab) => void;
  trustStatus?: string;
  onOpenTrace?: () => void;
  persistedObservations?: number;
}

const PRIMARY_MODES: { id: PlatformTab; number: string; label: string; sub: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'guide', number: '01', label: 'GUIDE', sub: 'Should I book?', icon: Sparkles },
  { id: 'market', number: '02', label: 'MARKET', sub: 'National Airfare State', icon: BarChart2 },
  { id: 'proof', number: '03', label: 'PROOF', sub: 'Verifiable Lineage', icon: ShieldCheck },
];

export const Header: React.FC<HeaderProps> = ({
  scope,
  runs,
  onSelectRun,
  activeTab = 'guide',
  onSelectTab,
  trustStatus = 'HIGH_CONFIDENCE',
  onOpenTrace,
  persistedObservations = 36606,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Normalize active tab to one of the 3 primary modes if legacy alias is provided
  const getNormalizedMode = (tab: PlatformTab): PlatformTab => {
    if (tab === 'overview' || tab === 'aeroguide' || tab === 'guide') return 'guide';
    if (tab === 'live-market' || tab === 'routes' || tab === 'horizon' || tab === 'market') return 'market';
    return 'proof';
  };

  const currentMode = getNormalizedMode(activeTab);

  return (
    <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur-xl sticky top-0 z-40 px-4 md:px-6 lg:px-8 shadow-2xl">
      <div className="max-w-[1600px] mx-auto py-3.5 flex items-center justify-between gap-4">
        {/* Left: Brand Monogram & Live Status */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => onSelectTab?.('guide')}
            className="flex items-center gap-3 text-left group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-2xl bg-blue-600 group-hover:bg-blue-500 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-600/30 ring-1 ring-blue-400/30 transition-all">
              <Plane className="w-5 h-5 transform -rotate-12" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-black tracking-tight text-white font-sans">
                  AeroCPI
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-500/20 text-cyan-300 border border-blue-500/30 uppercase">
                  v2026.1
                </span>
              </div>
              <div className="text-[11px] font-mono text-slate-400 hidden sm:block">
                National Airfare Intelligence Platform
              </div>
            </div>
          </button>

          {/* Live Data Pulse */}
          <div className="hidden xl:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>{persistedObservations.toLocaleString('en-IN')} PERSISTED OBSERVATIONS</span>
          </div>
        </div>

        {/* Center: The 3 Primary Modes ONLY */}
        <nav className="hidden md:flex items-center gap-2 bg-slate-900/90 border border-slate-800 p-1.5 rounded-2xl shadow-inner">
          {PRIMARY_MODES.map((mode) => {
            const Icon = mode.icon;
            const isSelected = currentMode === mode.id;
            return (
              <button
                key={mode.id}
                onClick={() => onSelectTab?.(mode.id)}
                className={`px-5 py-2 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-2.5 cursor-pointer ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 ring-1 ring-blue-400/50'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <span className={`text-[10px] opacity-75 font-mono ${isSelected ? 'text-blue-200' : 'text-slate-500'}`}>
                  {mode.number}
                </span>
                <Icon className="w-3.5 h-3.5" />
                <span>{mode.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right: Technical Run Context & Mobile Menu Toggle */}
        <div className="flex items-center gap-3">
          {/* Run Selector */}
          <div className="relative hidden sm:block">
            <select
              className="appearance-none bg-slate-900 hover:bg-slate-800/80 border border-slate-800 text-xs font-mono font-bold text-slate-300 rounded-xl pl-3 pr-8 py-2 focus:outline-none focus:border-cyan-500 cursor-pointer transition-colors"
              value={scope.run_id}
              onChange={(e) => onSelectRun(e.target.value)}
              aria-label="Select execution run"
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  Run: {r.run_id.substring(0, 8)}... ({r.reference_period})
                </option>
              ))}
            </select>
            <Database className="w-3 h-3 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Mobile Hamburger Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden py-4 border-t border-slate-800 space-y-2 font-mono text-sm">
          {PRIMARY_MODES.map((mode) => {
            const Icon = mode.icon;
            const isSelected = currentMode === mode.id;
            return (
              <button
                key={mode.id}
                onClick={() => {
                  onSelectTab?.(mode.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full p-3 rounded-xl flex items-center justify-between ${
                  isSelected ? 'bg-blue-600 text-white font-bold' : 'text-slate-300 bg-slate-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs opacity-60">{mode.number}</span>
                  <Icon className="w-4 h-4" />
                  <span>{mode.label}</span>
                </div>
                <span className="text-xs opacity-75">{mode.sub}</span>
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
