import React from 'react';
import { AlertTriangle, RefreshCw, FileQuestion } from 'lucide-react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="max-w-[1600px] mx-auto p-6 sm:p-8 space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="h-16 bg-white rounded-2xl border border-slate-200" />

      {/* Hero Skeleton */}
      <div className="h-48 bg-white rounded-2xl border border-slate-200" />

      {/* Map + Driver Grid Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 h-[460px] bg-white rounded-2xl border border-slate-200" />
        <div className="lg:col-span-5 h-[460px] bg-white rounded-2xl border border-slate-200" />
      </div>

      {/* Horizons Yield Curve Skeleton */}
      <div className="h-72 bg-white rounded-2xl border border-slate-200" />

      {/* Evidence Strip Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="h-56 bg-white rounded-2xl border border-slate-200" />
        <div className="h-56 bg-white rounded-2xl border border-slate-200" />
      </div>
    </div>
  );
};

interface ErrorViewProps {
  message: string;
  is404?: boolean;
  onRetry: () => void;
}

export const ErrorView: React.FC<ErrorViewProps> = ({ message, is404, onRetry }) => {
  return (
    <div className="max-w-xl mx-auto my-20 p-8 bg-white border border-slate-200 rounded-3xl shadow-xl text-center space-y-5">
      <div className="mx-auto w-14 h-14 rounded-2xl bg-red-50 border border-red-200 flex items-center justify-center text-red-600">
        {is404 ? <FileQuestion className="w-7 h-7" /> : <AlertTriangle className="w-7 h-7" />}
      </div>

      <div className="space-y-1.5">
        <h3 className="text-lg font-bold text-slate-900 font-mono tracking-tight">
          {is404 ? 'HTTP 404 — INDEX RUN NOT FOUND' : 'BACKEND SERVICE ERROR'}
        </h3>
        <p className="text-xs text-slate-500 font-sans leading-relaxed max-w-md mx-auto">
          {message}
        </p>
      </div>

      <div className="pt-3">
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-colors shadow-sm cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Loading Dashboard</span>
        </button>
      </div>
    </div>
  );
};
