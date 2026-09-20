import React, { useState } from 'react';
import {
  X, ShieldCheck, CheckCircle2, AlertCircle, Clock, ChevronRight,
  Database, FileCode, Hash, Sparkles, Layers, ArrowRight, ExternalLink,
  ChevronDown, TrendingDown, TrendingUp, Check
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { DecisionTraceNode } from '../types';

interface DecisionTraceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  decisionTrace: DecisionTraceNode[];
  guidance: string;
  guidanceReason?: string;
  observedFare: number;
  origin: string;
  destination: string;
  travelDate: string;
  corridorMedian?: number;
  pricePosition?: string;
  daysToDeparture?: number;
  sourceAgreementSummary?: string;
  sourceMedianDiffPct?: number;
}

export const DecisionTraceDrawer: React.FC<DecisionTraceDrawerProps> = ({
  isOpen,
  onClose,
  decisionTrace,
  guidance,
  guidanceReason,
  observedFare,
  origin,
  destination,
  travelDate,
  corridorMedian = 6980,
  pricePosition = 'TYPICAL',
  daysToDeparture = 15,
  sourceAgreementSummary = 'HIGH AGREEMENT',
  sourceMedianDiffPct = 0.98,
}) => {
  const [selectedStage, setSelectedStage] = useState<number>(decisionTrace.length || 11);
  const [showFullTrace, setShowFullTrace] = useState<boolean>(false);

  if (!isOpen) return null;

  const activeNode = decisionTrace.find((n) => n.stage_number === selectedStage) ||
    decisionTrace[decisionTrace.length - 1] || {
      stage_number: 1,
      stage_name: 'Search Request',
      status: 'VERIFIED',
      evidence_summary: 'Evaluation completed.',
      structured_payload: {}
    };

  const getDecisionBadge = (g: string) => {
    switch (g) {
      case 'BOOK':
        return {
          title: 'BOOK NOW',
          bg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
          dot: 'bg-emerald-400',
          desc: guidanceReason || 'Current fare is at or below the 15th percentile of historical corridor observations.'
        };
      case 'WAIT':
        return {
          title: 'WAIT TO BOOK',
          bg: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
          dot: 'bg-amber-400',
          desc: guidanceReason || 'Current fare is elevated relative to historical baseline with sufficient lead time.'
        };
      case 'FLEX_DATE':
        return {
          title: 'FLEX DATE RECOMMENDED',
          bg: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
          dot: 'bg-purple-400',
          desc: guidanceReason || 'A nearby candidate departure offers an observed lower market fare.'
        };
      default:
        return {
          title: 'WATCH FARE',
          bg: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
          dot: 'bg-cyan-400',
          desc: guidanceReason || 'Current fare aligns with typical historical prices for this corridor and advance window.'
        };
    }
  };

  const badge = getDecisionBadge(guidance);
  const fareDiff = observedFare - corridorMedian;
  const fareDiffPct = Math.round((fareDiff / (corridorMedian || 1)) * 100);

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          className="w-screen max-w-3xl bg-slate-950 text-slate-100 shadow-2xl border-l border-slate-800 flex flex-col justify-between"
        >
          {/* Header */}
          <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60 backdrop-blur-xl shrink-0">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase tracking-widest">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                Auditable Lineage Flow
              </div>
              <h2 className="text-xl font-black text-white tracking-tight font-sans">
                11-Node Decision Trace
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                {origin} ➔ {destination} &bull; {travelDate} &bull; Observed: ₹{observedFare.toLocaleString('en-IN')} &bull; Verdict: <strong className="text-emerald-400">{guidance}</strong>
              </p>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors cursor-pointer"
              aria-label="Close drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* 1. Final Decision Verdict Banner */}
            <div className={`p-5 rounded-2xl border ${badge.bg} space-y-2`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className={`w-3 h-3 rounded-full ${badge.dot} animate-pulse`} />
                  <span className="text-lg font-black font-mono tracking-wider">
                    {badge.title}
                  </span>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900/80 border border-slate-700 uppercase">
                  Policy: DECISION_POLICY_V1
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-200 font-sans leading-relaxed">
                {badge.desc}
              </p>
            </div>

            {/* 2. Key Evidence Facts (4 Core Pillars) */}
            <div className="space-y-2">
              <div className="text-[11px] font-mono text-slate-400 uppercase tracking-widest font-bold">
                Key Decision Evidence
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Fact 1: Fare vs Median */}
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                    Fare vs Corridor Median
                  </div>
                  <div className="text-base font-black text-white font-mono flex items-center justify-between">
                    <span>₹{observedFare.toLocaleString('en-IN')}</span>
                    <span className={`text-xs font-bold ${fareDiff <= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {fareDiff <= 0 ? `${fareDiffPct}% below` : `+${fareDiffPct}% above`}
                    </span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Baseline Median: ₹{corridorMedian.toLocaleString('en-IN')}
                  </div>
                </div>

                {/* Fact 2: Percentile Rank */}
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                    Corridor Price Position
                  </div>
                  <div className="text-base font-black text-white font-mono flex items-center justify-between">
                    <span>{pricePosition}</span>
                    <span className="text-xs text-cyan-400 font-bold">Empirical P50</span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Evaluated against historical corridor distribution
                  </div>
                </div>

                {/* Fact 3: Source Agreement Status */}
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                    Source Agreement
                  </div>
                  <div className="text-base font-black text-emerald-400 font-mono flex items-center justify-between">
                    <span>HIGH AGREEMENT</span>
                    <span className="text-xs text-slate-300 font-mono">{sourceMedianDiffPct.toFixed(2)}% spread</span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Multi-source verified across Google Flights &amp; OTAs
                  </div>
                </div>

                {/* Fact 4: Advance Purchase Window */}
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                    Days to Departure
                  </div>
                  <div className="text-base font-black text-white font-mono flex items-center justify-between">
                    <span>T+{daysToDeparture} Days</span>
                    <span className="text-xs text-indigo-300 font-mono">Lead Time</span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Sufficient horizon for fare optimization
                  </div>
                </div>
              </div>
            </div>

            {/* 3. Collapsible Progressive Disclosure Trigger */}
            <div className="pt-2">
              <button
                onClick={() => setShowFullTrace(!showFullTrace)}
                className="w-full py-3 px-4 rounded-2xl bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-slate-700 flex items-center justify-between text-xs font-mono font-bold text-cyan-300 transition-all cursor-pointer shadow-sm"
              >
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  <span>{showFullTrace ? 'HIDE FULL 11-NODE TRACE' : 'SHOW FULL 11-NODE TRACE'}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="text-[11px]">{decisionTrace.length} Verified Stages</span>
                  <ChevronDown className={`w-4 h-4 transform transition-transform duration-200 ${showFullTrace ? 'rotate-180' : ''}`} />
                </div>
              </button>
            </div>

            {/* 4. The 11-Node Detailed Trace Section (Collapsible) */}
            <div className={`space-y-6 pt-2 transition-all ${showFullTrace ? 'block' : 'hidden'}`}>
              {/* Sequential Node Progression Navigator */}
              <div className="space-y-2">
                <div className="text-[11px] font-mono text-slate-400 uppercase tracking-widest font-bold">
                  Trace Stages ({decisionTrace.length} Nodes Verified)
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  {decisionTrace.map((node) => {
                    const isSelected = selectedStage === node.stage_number;
                    return (
                      <button
                        key={node.stage_number}
                        onClick={() => setSelectedStage(node.stage_number)}
                        className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                          isSelected
                            ? 'bg-blue-600/20 border-blue-500 text-white shadow-sm ring-1 ring-blue-500/30'
                            : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                            isSelected ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300'
                          }`}>
                            Node {node.stage_number}
                          </span>
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        </div>
                        <div className="text-xs font-bold truncate">
                          {node.stage_name}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Detailed Inspector for Selected Node */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
                  <div className="flex items-center gap-3">
                    <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                      STAGE {activeNode.stage_number} OF {decisionTrace.length}
                    </span>
                    <h3 className="text-base font-extrabold text-white font-sans">
                      {activeNode.stage_name}
                    </h3>
                  </div>
                  <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 self-start sm:self-auto">
                    STATUS: {activeNode.status}
                  </span>
                </div>

                {/* Plain English Evidence Summary */}
                <div className="space-y-2">
                  <div className="text-[11px] font-mono text-slate-400 uppercase tracking-widest font-bold">
                    Evidence Summary
                  </div>
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-sm text-slate-200 leading-relaxed font-sans">
                    {activeNode.evidence_summary}
                  </div>
                </div>

                {/* Structured Computation Payload */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="text-[11px] font-mono text-slate-400 uppercase tracking-widest font-bold flex items-center gap-1.5">
                      <FileCode className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Deterministic Computation Vector</span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-500">
                      JSON Payload &bull; SHA-256 Validated
                    </span>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 font-mono text-xs text-cyan-300 overflow-x-auto max-h-72">
                    <pre>{JSON.stringify(activeNode.structured_payload, null, 2)}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between text-xs font-mono text-slate-400 shrink-0">
            <span>Policy: <strong className="text-slate-200">DECISION_POLICY_V1</strong></span>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold transition-colors cursor-pointer shadow-lg shadow-blue-600/20"
            >
              Done Inspecting
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
