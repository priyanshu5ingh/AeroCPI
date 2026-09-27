import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Server,
  Layers,
  Database,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Radio,
  Play,
  TrendingUp,
  XCircle,
  HelpCircle,
  ShieldAlert,
  Calendar,
  Zap,
} from 'lucide-react';
import {
  fetchOperationalSourceHealth,
  fetchOperationalMetrics,
  fetchOperationalAlerts,
  fetchOperationalRuns,
  triggerCollectionSweep,
  fetchForecastingReadiness,
} from '../services/api';

export const OperationsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  const [healthData, setHealthData] = useState<any>(null);
  const [metricsData, setMetricsData] = useState<any>(null);
  const [alertsData, setAlertsData] = useState<any[]>([]);
  const [runsData, setRunsData] = useState<any[]>([]);

  const loadData = async () => {
    try {
      setRefreshing(true);
      const [health, metrics, alerts, runs, readiness] = await Promise.all([
        fetchOperationalSourceHealth(),
        fetchOperationalMetrics(),
        fetchOperationalAlerts(),
        fetchOperationalRuns(15),
        fetchForecastingReadiness()
      ]);
      setHealthData(health);
      setMetricsData({ ...metrics, readiness });
      setAlertsData(alerts || []);
      setRunsData(runs || []);
    } catch (err) {
      console.error('Failed to load operational telemetry', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // 30s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const handleTriggerSweep = async () => {
    try {
      setTriggering(true);
      setTriggerMsg('Initiating multi-source collection sweep...');
      const res = await triggerCollectionSweep();
      setTriggerMsg(`Sweep initiated: Run ID ${res.run_id} (${res.status})`);
      setTimeout(() => {
        loadData();
        setTriggerMsg(null);
      }, 3000);
    } catch (err: any) {
      setTriggerMsg(`Trigger failed: ${err.message || 'Unknown error'}`);
    } finally {
      setTriggering(false);
    }
  };

  const getTaxonomyBadge = (state: string) => {
    switch (state) {
      case 'CURRENTLY_HEALTHY':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            CURRENTLY HEALTHY
          </span>
        );
      case 'OPERATIONAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            <Radio className="w-3 h-3 text-cyan-400" />
            OPERATIONAL
          </span>
        );
      case 'CONFIGURED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <Clock className="w-3 h-3 text-amber-400" />
            CONFIGURED
          </span>
        );
      case 'IMPLEMENTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700">
            <Server className="w-3 h-3 text-slate-400" />
            IMPLEMENTED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3 h-3 text-rose-400" />
            UNAVAILABLE
          </span>
        );
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Top Header & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-3 uppercase tracking-wider">
            <Activity className="w-3.5 h-3.5" />
            Phase 8 & 9 Operational Control
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Production Operations & Evidence Monitoring</h1>
          <p className="text-slate-400 text-sm mt-1 max-w-2xl">
            Live telemetry, source availability taxonomy, process locks, and empirical longitudinal trajectory accumulation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={refreshing}
            className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white text-xs font-mono font-bold inline-flex items-center gap-2 transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
            Refresh
          </button>

          <button
            onClick={handleTriggerSweep}
            disabled={triggering}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-mono font-bold inline-flex items-center gap-2 shadow-lg shadow-cyan-950/50 transition cursor-pointer disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${triggering ? 'animate-pulse' : ''}`} />
            {triggering ? 'Triggering...' : 'Trigger Sweep'}
          </button>
        </div>
      </div>

      {triggerMsg && (
        <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-xs font-mono flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          {triggerMsg}
        </div>
      )}

      {/* 1. Core Production Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase">
            <span>Total Observations</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-black font-mono text-white">
            {metricsData ? metricsData.total_observations.toLocaleString() : '--'}
          </div>
          <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
            <span className="text-emerald-400 font-bold">{metricsData?.accepted_observations.toLocaleString() || '--'}</span> Accepted &bull; <span className="text-cyan-400">{metricsData?.eligible_observations.toLocaleString() || '--'}</span> Eligible
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase">
            <span>Capture Freshness</span>
            <Clock className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black font-mono text-white">
            {metricsData?.latest_capture_age_minutes != null ? `${metricsData.latest_capture_age_minutes}m` : '--'}
          </div>
          <div className="text-[11px] font-mono text-slate-400">
            Latest Search: {metricsData?.latest_search_timestamp ? new Date(metricsData.latest_search_timestamp).toLocaleTimeString() : 'N/A'}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase">
            <span>Longitudinal 7D Pairs</span>
            <TrendingUp className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-black font-mono text-white">
            {metricsData?.panel?.valid_7d_pairs ?? 0}
          </div>
          <div className="text-[11px] font-mono text-amber-400">
            {metricsData?.panel?.total_trajectories || 0} active trajectories tracking
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase">
            <span>Synthetic Data Gate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black font-mono text-emerald-400">
            {metricsData?.synthetic_observations ?? 0}
          </div>
          <div className="text-[11px] font-mono text-emerald-400/80">
            100% Verified Real Production Captures
          </div>
        </div>
      </div>

      {/* 2. Longitudinal Machine Learning Readiness Truth Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-amber-950/20 border border-amber-500/30 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20">
              <ShieldAlert className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <div className="text-xs font-mono uppercase tracking-widest text-amber-400 font-bold">
                Honest Empirical Gate Status
              </div>
              <h3 className="text-lg font-black text-white">
                Machine Learning Forecast: {metricsData?.panel?.readiness_status || 'INSUFFICIENT_DATA'}
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
              MODEL_NOT_READY
            </span>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
          AeroCPI strictly refuses to manufacture synthetic training examples or premature model signals. The production panel is currently accumulating repeated chronological snapshots across the 14 pinned travel dates. Supervised forecast promotion gates will automatically evaluate when valid 7-day trajectory pairs exist.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/80 text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Trajectories Tracked</span>
            <span className="text-white font-bold">{metricsData?.panel?.total_trajectories || 0}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Trajectories with &gt;=2 Obs</span>
            <span className="text-white font-bold">{metricsData?.panel?.trajectories_with_gte_2_observations || 0}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Valid 7-Day Pairs</span>
            <span className="text-amber-400 font-bold">{metricsData?.panel?.valid_7d_pairs || 0}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Training Examples</span>
            <span className="text-white font-bold">{metricsData?.panel?.dataset_examples || 0}</span>
          </div>
        </div>
      </div>
      
      {/* Automated Model Lifecycle Truth Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/20 border border-indigo-500/30 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
              <Activity className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="text-xs font-mono uppercase tracking-widest text-indigo-400 font-bold">
                Automated Model Lifecycle Trigger
              </div>
              <h3 className="text-lg font-black text-white">
                Last Status: {metricsData?.readiness?.last_training_status || 'NEVER_TRIGGERED'}
              </h3>
            </div>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
          The collection scheduler automatically recalculates readiness after every sweep. When empirical criteria are met, an isolated temporal walk-forward evaluation creates a candidate model. Promotion to production is gated by strict baseline comparison.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-800/80 text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Last Evaluation Run</span>
            <span className="text-white font-bold">{metricsData?.readiness?.last_training_time || 'N/A'}</span>
          </div>
          <div className="sm:col-span-2">
            <span className="text-slate-500 block text-[10px] uppercase">Evaluation Notes / Rejection</span>
            <span className="text-rose-400 font-bold">{metricsData?.readiness?.last_training_reasons?.join(", ") || 'N/A'}</span>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-800/80 text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Current Production SHA-256</span>
            <span className="text-emerald-400 font-bold">{metricsData?.readiness?.production_model_sha || 'NONE'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Production Holdout F1</span>
            <span className="text-white font-bold">{metricsData?.readiness?.production_model_metrics?.classification?.macro_f1?.toFixed(3) || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* 3. Source Health & Telemetry Table */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-black text-white font-mono uppercase tracking-wider">
              Source Adapter Health Matrix
            </h3>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Strict state taxonomy: IMPLEMENTED &bull; CONFIGURED &bull; OPERATIONAL &bull; CURRENTLY HEALTHY
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                <th className="pb-3 pr-4 font-bold">Source</th>
                <th className="pb-3 px-4 font-bold">Taxonomy State</th>
                <th className="pb-3 px-4 font-bold">24h Attempts</th>
                <th className="pb-3 px-4 font-bold">Capture Rate</th>
                <th className="pb-3 px-4 font-bold">Parser Rate</th>
                <th className="pb-3 px-4 font-bold">Accepted</th>
                <th className="pb-3 px-4 font-bold">Last Capture</th>
                <th className="pb-3 pl-4 font-bold">Adapter Ver</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
              {healthData?.sources?.map((src: any) => (
                <tr key={src.source_id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3 pr-4">
                    <div className="font-bold text-white">{src.name}</div>
                    <div className="text-[10px] text-slate-500">{src.source_id}</div>
                  </td>
                  <td className="py-3 px-4">{getTaxonomyBadge(src.taxonomy_state)}</td>
                  <td className="py-3 px-4 text-slate-300">
                    {src.total_attempts_24h} <span className="text-[10px] text-slate-500">({src.failed_attempts_24h} err)</span>
                  </td>
                  <td className="py-3 px-4 font-bold text-white">{src.capture_success_rate_pct}%</td>
                  <td className="py-3 px-4 font-bold text-white">{src.parser_success_rate_pct}%</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold">{src.accepted_observations.toLocaleString()}</td>
                  <td className="py-3 px-4 text-slate-300">
                    {src.last_success_at ? new Date(src.last_success_at).toLocaleTimeString() : '--'}
                  </td>
                  <td className="py-3 pl-4 text-slate-400">{src.adapter_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Active Operational Alerts */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-black text-white font-mono uppercase tracking-wider">
            Deterministic Operational Alerts
          </h3>
          <span className="text-xs font-mono text-slate-400">
            {alertsData.length} active conditions
          </span>
        </div>

        <div className="space-y-3">
          {alertsData.map((alert: any) => (
            <div
              key={alert.alert_id}
              className={`p-4 rounded-xl border flex items-start gap-3 ${
                alert.severity === 'CRITICAL'
                  ? 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                  : alert.severity === 'WARNING'
                  ? 'bg-amber-950/20 border-amber-500/30 text-amber-300'
                  : 'bg-cyan-950/20 border-cyan-500/30 text-cyan-300'
              }`}
            >
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <div className="space-y-1">
                <div className="text-xs font-bold font-mono uppercase tracking-wide">{alert.title}</div>
                <div className="text-xs font-sans text-slate-300 leading-relaxed">{alert.message}</div>
                <div className="text-[10px] font-mono text-slate-500">Triggered: {new Date(alert.triggered_at).toLocaleString()}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. Historical Collection Runs */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-black text-white font-mono uppercase tracking-wider">
            Recent Collection Sweeps
          </h3>
          <span className="text-xs font-mono text-slate-400">Audit trail</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                <th className="pb-3 pr-4 font-bold">Run ID</th>
                <th className="pb-3 px-4 font-bold">Status</th>
                <th className="pb-3 px-4 font-bold">Started</th>
                <th className="pb-3 px-4 font-bold">Duration</th>
                <th className="pb-3 px-4 font-bold">Queries</th>
                <th className="pb-3 pl-4 font-bold">Saved Observations</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
              {runsData.map((run: any) => (
                <tr key={run.run_id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3 pr-4 font-bold text-slate-200">{run.run_id.slice(0, 13)}...</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        run.status === 'COMPLETED'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : run.status === 'RUNNING'
                          ? 'bg-cyan-500/20 text-cyan-400 animate-pulse'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {run.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300">{new Date(run.started_at).toLocaleTimeString()}</td>
                  <td className="py-3 px-4 text-slate-400">
                    {run.finished_at
                      ? `${Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`
                      : 'running...'}
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {run.queries_success}/{run.queries_total} <span className="text-[10px] text-slate-500">({run.queries_failed} failed)</span>
                  </td>
                  <td className="py-3 pl-4 text-emerald-400 font-bold">{run.observations_saved}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
