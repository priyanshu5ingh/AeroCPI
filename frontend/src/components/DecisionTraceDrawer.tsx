import React, { useState } from 'react';
import {
  X, ShieldCheck, CheckCircle2, AlertCircle, Clock, ChevronRight,
  Database, FileCode, Hash, Sparkles, Layers, ArrowRight, ExternalLink
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { DecisionTraceNode } from '../types';

interface DecisionTraceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  decisionTrace: DecisionTraceNode[];
  guidance: string;
  observedFare: number;
  origin: string;
  destination: string;
  travelDate: string;
}

export const DecisionTraceDrawer: React.FC<DecisionTraceDrawerProps> = ({
  isOpen,
  onClose,
  decisionTrace,
  guidance,
  observedFare,
  origin,
  destination,
  travelDate,
}) => {
  const [selectedStage, setSelectedStage] = useState<number>(decisionTrace.length || 11);

  if (!isOpen) return null;

  const activeNode = decisionTrace.find((n) => n.stage_number === selectedStage) ||
    decisionTrace[decisionTrace.length - 1] || {
      stage_number: 1,
      stage_name: 'Search Request',
      status: 'VERIFIED',
      evidence_summary: 'Evaluation completed.',
      structured_payload: {}
    };

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
          <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60 backdrop-blur-xl">
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

          {/* Footer */}
          <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Policy: <strong className="text-slate-200">DECISION_POLICY_V1</strong></span>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold transition-colors cursor-pointer"
            >
              Done Inspecting
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
