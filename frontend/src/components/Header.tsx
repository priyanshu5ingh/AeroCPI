import React, { useState } from 'react';
import {
  Plane, Calendar, Layers, Database, LayoutDashboard, Compass, Clock, BookOpen,
  Filter, ShieldCheck, Search, FlaskConical, GitCommit, ShieldAlert, Menu, X, Check
} from 'lucide-react';
import { DashboardScope, SimpleIndexRun } from '../types';
import { AnimatePresence, motion } from 'framer-motion';
import { drawerVariants, drawerBackdropVariants } from '../lib/motion';

export type PlatformTab =
  | 'overview'
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
}

const TABS: { id: PlatformTab; label: string; short: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'overview', label: 'Overview', short: 'Overview', icon: LayoutDashboard },
  { id: 'live-market', label: 'Observation Explorer', short: 'Explorer', icon: Search },
  { id: 'routes', label: 'Route Intelligence', short: 'Routes', icon: Compass },
  { id: 'horizon', label: 'Horizon Analysis', short: 'Horizon', icon: Clock },
  { id: 'data-quality', label: 'Data Quality', short: 'Quality', icon: Filter },
  { id: 'methodology', label: 'Methodology Studio', short: 'Methodology', icon: BookOpen },
  { id: 'validation', label: 'Validation Lab', short: 'Validation', icon: FlaskConical },
  { id: 'audit', label: 'Audit & Trace', short: 'Audit', icon: ShieldCheck },
];

export const Header: React.FC<HeaderProps> = ({
  scope,
  runs,
  onSelectRun,
  activeTab = 'overview',
  onSelectTab,
  trustStatus = 'UNEVALUATED',
  onOpenTrace,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const activeLabel = TABS.find(t => t.id === activeTab)?.label || 'Overview';

  return (
    <header className="border-b border-slate-200/85 bg-white/90 backdrop-blur-xl sticky top-0 z-40 px-4 md:px-6 lg:px-8 shadow-[0_1px_3px_0_rgba(15,23,42,0.03)]">
      
      {/* DESKTOP & TABLET */}
      <div className="hidden md:block max-w-[1600px] mx-auto py-3 space-y-3">
        {/* Top Tier: Brand Identity & Active Run Metadata */}
        <div className="flex flex-row items-center justify-between gap-3">
          {/* Brand Monogram */}
          <div className="flex items-center gap-3.5">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-sm shadow-blue-500/25 ring-2 ring-blue-500/20">
              <Plane className="w-5 h-5 transform -rotate-12" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-extrabold tracking-tight text-slate-900 font-sans">
                  AeroCPI
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200/80 uppercase">
                  v2026.1
                </span>
                <span className="text-xs font-semibold text-slate-500 hidden lg:inline ml-2">
                  India Airfare Price Index &amp; Measurement Observatory
                </span>
              </div>
            </div>
          </div>

          {/* Context Controls */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <select
                className="appearance-none bg-slate-50/50 hover:bg-slate-50 border border-slate-200 text-sm font-semibold text-slate-800 rounded-xl pl-3 pr-9 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 cursor-pointer shadow-xs transition-colors"
                value={scope.run_id}
                onChange={(e) => onSelectRun(e.target.value)}
                aria-label="Select execution run"
              >
                {runs.map(r => (
                  <option key={r.run_id} value={r.run_id}>
                    Run: {r.run_id.substring(0, 8)}... 
                  </option>
                ))}
              </select>
              <Database className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            <div className="flex items-center gap-1.5 bg-slate-50/90 border border-slate-200/80 rounded-xl px-2.5 py-1.5 font-mono font-medium text-slate-700 shadow-xs">
              <Layers className="w-3.5 h-3.5 text-emerald-600" />
              <span>{scope.cabin}</span>
            </div>

            <div className="flex items-center gap-1.5 bg-amber-50/80 border border-amber-200/90 rounded-xl px-2.5 py-1.5 font-mono text-[11px] font-bold text-amber-800 shadow-xs">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
              <span>TRUST: {trustStatus}</span>
            </div>
          </div>
        </div>

        {/* Navigation Tier */}
        <nav className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-hide" aria-label="Main Navigation">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => onSelectTab && onSelectTab(tab.id)}
                className={`relative flex items-center gap-2 px-2.5 lg:px-3.5 py-2 rounded-xl text-xs font-bold transition-colors whitespace-nowrap cursor-pointer z-10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 ${
                  isActive
                    ? 'text-white'
                    : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100/50'
                }`}
                aria-current={isActive ? 'page' : undefined}
              >
                {isActive && (
                  <motion.div
                    layoutId="header-active-tab"
                    className="absolute inset-0 bg-slate-900 rounded-xl shadow-md border border-slate-800/80 -z-10"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <Icon className="w-3.5 h-3.5 relative z-10" />
                <span className="relative z-10 hidden lg:inline">{tab.label}</span>
                <span className="relative z-10 lg:hidden">{tab.short}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* MOBILE */}
      <div className="md:hidden flex items-center justify-between py-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-sm">
            <Plane className="w-4 h-4 transform -rotate-12" />
          </div>
          <span className="font-extrabold text-slate-900 tracking-tight">AeroCPI</span>
        </div>
        
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-slate-600 truncate">{activeLabel}</span>
          <button 
            onClick={() => setMobileMenuOpen(true)}
            className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
            aria-label="Open mobile menu"
            aria-expanded={mobileMenuOpen}
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* MOBILE NAV OVERLAY */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div 
              variants={drawerBackdropVariants}
              initial="initial" animate="animate" exit="exit"
              onClick={() => setMobileMenuOpen(false)}
              className="fixed inset-0 bg-slate-900/60 z-50 md:hidden"
              aria-hidden="true"
            />
            <motion.div
              variants={drawerVariants}
              initial="initial" animate="animate" exit="exit"
              className="fixed inset-y-0 right-0 w-4/5 max-w-xs bg-white/95 backdrop-blur-xl z-50 flex flex-col border-l border-slate-200 shadow-2xl md:hidden"
              role="dialog"
              aria-modal="true"
              aria-label="Mobile Navigation Menu"
            >
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <span className="font-bold text-slate-900">Menu</span>
                <button 
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                  aria-label="Close mobile menu"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {/* Context */}
                <div className="space-y-3">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Run Context</p>
                  <select
                    className="w-full appearance-none bg-slate-50 hover:bg-slate-100 border border-slate-200 text-sm font-semibold text-slate-800 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-xs"
                    value={scope.run_id}
                    onChange={(e) => {
                      onSelectRun(e.target.value);
                      setMobileMenuOpen(false);
                    }}
                    aria-label="Select execution run"
                  >
                    {runs.map(r => (
                      <option key={r.run_id} value={r.run_id}>
                        {r.run_id.substring(0, 8)} 
                      </option>
                    ))}
                  </select>
                  
                  <div className="flex gap-2">
                    <div className="flex-1 flex items-center justify-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl py-1.5 font-mono text-xs font-medium text-slate-700">
                      <Layers className="w-3.5 h-3.5 text-emerald-600" /> {scope.cabin}
                    </div>
                    <div className="flex-1 flex items-center justify-center gap-1.5 bg-amber-50 border border-amber-200 rounded-xl py-1.5 font-mono text-[10px] font-bold text-amber-800">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-600" /> {trustStatus}
                    </div>
                  </div>
                </div>

                {/* Nav Links */}
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Modules</p>
                  {TABS.map((tab) => {
                    const isActive = activeTab === tab.id;
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => {
                          if (onSelectTab) onSelectTab(tab.id);
                          setMobileMenuOpen(false);
                        }}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 ${
                          isActive
                            ? 'bg-blue-50 text-blue-700 border border-blue-100'
                            : 'text-slate-600 hover:bg-slate-50'
                        }`}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        <Icon className="w-4 h-4" />
                        <span>{tab.label}</span>
                        {isActive && <Check className="w-4 h-4 ml-auto text-blue-600" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </header>
  );
};
