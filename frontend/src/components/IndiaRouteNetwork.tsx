import React, { useState } from 'react';
import { Plane, ArrowRight, ExternalLink } from 'lucide-react';
import { DriverSummary } from '../types';

interface IndiaRouteNetworkProps {
  drivers?: DriverSummary;
  onSelectRoute?: (routeId: string) => void;
}

interface RouteVisual {
  id: string;
  origin: string;
  destination: string;
  pathD: string;
  color: string;
  strokeWidth: number;
  dashArray?: string;
  defaultFareShift: string;
  defaultIndex: string;
  defaultWeight: string;
  percentShift: string;
  contributionText: string;
  isPositive: boolean;
  statusText: string;
}

const ROUTES_DATA: RouteVisual[] = [
  {
    id: 'DEL-HYD',
    origin: 'DEL',
    destination: 'HYD',
    pathD: 'M 260 145 Q 285 220 280 295',
    color: '#10B981', // Emerald
    strokeWidth: 3.2,
    defaultFareShift: '₹8,825 → ₹9,807',
    defaultIndex: '111.13',
    defaultWeight: '10.3%',
    percentShift: '+11.1%',
    contributionText: '+1.07',
    isPositive: true,
    statusText: 'Upward index contribution (+11.1% fare shift)'
  },
  {
    id: 'GOI-BOM',
    origin: 'GOI',
    destination: 'BOM',
    pathD: 'M 195 345 Q 185 315 190 280',
    color: '#EF4444', // Coral-red
    strokeWidth: 3.8,
    defaultFareShift: '₹9,539 → ₹5,230',
    defaultIndex: '54.83',
    defaultWeight: '8.0%',
    percentShift: '-45.2%',
    contributionText: '-4.74',
    isPositive: false,
    statusText: 'Negative index contribution (-45.2% fare shift)'
  },
  {
    id: 'BLR-DEL',
    origin: 'BLR',
    destination: 'DEL',
    pathD: 'M 255 375 Q 275 260 260 145',
    color: '#F87171',
    strokeWidth: 2.6,
    dashArray: '4 2',
    defaultFareShift: '₹10,480 → ₹9,900',
    defaultIndex: '94.47',
    defaultWeight: '13.2%',
    percentShift: '-5.5%',
    contributionText: '-0.79',
    isPositive: false,
    statusText: 'Negative index contribution (-5.5% fare shift)'
  },
  {
    id: 'BOM-DEL',
    origin: 'BOM',
    destination: 'DEL',
    pathD: 'M 190 280 Q 210 210 260 145',
    color: '#94A3B8',
    strokeWidth: 3.5,
    defaultFareShift: '₹6,450 → ₹6,380',
    defaultIndex: '98.91',
    defaultWeight: '18.1%',
    percentShift: '-1.1%',
    contributionText: '-0.22',
    isPositive: false,
    statusText: 'Negative index contribution (-1.1% fare shift)'
  },
  {
    id: 'MAA-DEL',
    origin: 'MAA',
    destination: 'DEL',
    pathD: 'M 305 370 Q 315 265 260 145',
    color: '#F87171',
    strokeWidth: 2.2,
    dashArray: '3 3',
    defaultFareShift: '₹8,120 → ₹7,850',
    defaultIndex: '96.67',
    defaultWeight: '8.9%',
    percentShift: '-3.3%',
    contributionText: '-0.30',
    isPositive: false,
    statusText: 'Negative index contribution (-3.3% fare shift)'
  },
  {
    id: 'DEL-CCU',
    origin: 'DEL',
    destination: 'CCU',
    pathD: 'M 260 145 Q 340 175 420 210',
    color: '#CBD5E1',
    strokeWidth: 2.0,
    defaultFareShift: '₹7,150 → ₹7,010',
    defaultIndex: '98.04',
    defaultWeight: '7.4%',
    percentShift: '-2.0%',
    contributionText: '-0.15',
    isPositive: false,
    statusText: 'Negative index contribution (-2.0% fare shift)'
  },
  {
    id: 'BLR-CCU',
    origin: 'BLR',
    destination: 'CCU',
    pathD: 'M 255 375 Q 355 310 420 210',
    color: '#10B981',
    strokeWidth: 2.2,
    defaultFareShift: '₹7,800 → ₹8,250',
    defaultIndex: '105.77',
    defaultWeight: '6.8%',
    percentShift: '+5.8%',
    contributionText: '+0.33',
    isPositive: true,
    statusText: 'Positive index contribution (+5.8% fare shift)'
  },
  {
    id: 'BLR-HYD',
    origin: 'BLR',
    destination: 'HYD',
    pathD: 'M 255 375 Q 265 335 280 295',
    color: '#10B981',
    strokeWidth: 2.2,
    defaultFareShift: '₹3,950 → ₹4,210',
    defaultIndex: '106.58',
    defaultWeight: '7.2%',
    percentShift: '+6.6%',
    contributionText: '+0.28',
    isPositive: true,
    statusText: 'Positive index contribution (+6.6% fare shift)'
  },
  {
    id: 'BOM-BLR',
    origin: 'BOM',
    destination: 'BLR',
    pathD: 'M 190 280 Q 210 330 255 375',
    color: '#10B981',
    strokeWidth: 2.4,
    defaultFareShift: '₹4,600 → ₹4,630',
    defaultIndex: '100.65',
    defaultWeight: '8.5%',
    percentShift: '+0.7%',
    contributionText: '+0.03',
    isPositive: true,
    statusText: 'Positive index contribution (+0.7% fare shift)'
  },
  {
    id: 'GOI-DEL',
    origin: 'GOI',
    destination: 'DEL',
    pathD: 'M 195 345 Q 210 240 260 145',
    color: '#CBD5E1',
    strokeWidth: 1.8,
    dashArray: '2 3',
    defaultFareShift: '₹6,800 → ₹6,800',
    defaultIndex: '100.00',
    defaultWeight: '4.8%',
    percentShift: '0.0%',
    contributionText: '0.00',
    isPositive: false,
    statusText: 'Zero net contribution (0.0% fare shift)'
  }
];

const METRO_NODES = [
  { code: 'DEL', name: 'Delhi Indira Gandhi', x: 260, y: 145, labelX: 12, labelY: 4, nameX: 12, nameY: 15, color: '#1D6AE5' },
  { code: 'BOM', name: 'Mumbai CSMIA', x: 190, y: 280, labelX: -48, labelY: 4, nameX: -68, nameY: 15, color: '#0F172A' },
  { code: 'HYD', name: 'Hyderabad RGIA', x: 280, y: 295, labelX: 12, labelY: 3, nameX: 12, nameY: 14, color: '#10B981' },
  { code: 'BLR', name: 'Bengaluru Kempegowda', x: 255, y: 375, labelX: -42, labelY: 5, nameX: -76, nameY: 16, color: '#1D6AE5' },
  { code: 'CCU', name: 'Kolkata NSCBI', x: 420, y: 210, labelX: 10, labelY: 4, nameX: 10, nameY: 15, color: '#0F172A' },
  { code: 'MAA', name: 'Chennai Intl', x: 305, y: 370, labelX: 10, labelY: 4, nameX: 10, nameY: 15, color: '#0F172A' },
  { code: 'GOI', name: 'Goa Dabolim', x: 195, y: 345, labelX: -38, labelY: 2, nameX: -46, nameY: 13, color: '#EF4444' }
];

export const IndiaRouteNetwork: React.FC<IndiaRouteNetworkProps> = ({ drivers, onSelectRoute }) => {
  const [activeRouteId, setActiveRouteId] = useState<string>('DEL-HYD');

  const activeRoute = ROUTES_DATA.find((r) => r.id === activeRouteId) || ROUTES_DATA[0];

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-[0_2px_12px_-1px_rgba(15,23,42,0.03)] p-6 sm:p-7 flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              India Route Network
            </h2>
            <span className="text-xs font-semibold text-slate-500 bg-slate-50 px-2.5 py-0.5 rounded-full border border-slate-200/60">
              DGCA-Weighted Route Basket
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Equirectangular Conformal Arc Projection · 10 DGCA Basket Trunk Routes
          </p>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500">
          <span className="font-mono">10 Routes</span>
          <span>·</span>
          <span>7 Metro Hubs</span>
        </div>
      </div>

      {/* Interactive Map Graphic Canvas */}
      <div className="relative flex-1 min-h-[440px] flex items-center justify-center my-3 overflow-hidden rounded-xl bg-[#FAFBFD] border border-slate-100">
        {/* Background Coordinate Grid */}
        <svg className="absolute inset-0 w-full h-full stroke-slate-200/30 pointer-events-none" width="100%" height="100%">
          <defs>
            <pattern id="networkGrid" width="36" height="36" patternUnits="userSpaceOnUse">
              <path d="M 36 0 L 0 0 0 36" fill="none" stroke="currentColor" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#networkGrid)" />
        </svg>

        {/* India Geodesic Route Map */}
        <svg
          viewBox="0 0 600 480"
          className="relative w-full h-[420px] max-w-[580px] select-none"
          fill="none"
        >
          {/* India Landmass Abstract Silhouette */}
          <path
            d="M 270 45 C 310 50, 360 90, 350 130 C 370 140, 420 150, 430 170 C 440 190, 410 210, 405 230 C 380 260, 370 300, 350 340 C 320 390, 280 430, 260 450 C 240 430, 210 370, 190 320 C 180 290, 175 250, 160 220 C 145 190, 170 170, 190 150 C 210 130, 240 60, 270 45 Z"
            fill="#F1F4F9"
            opacity="0.85"
            stroke="#CBD5E1"
            strokeWidth="1.2"
            strokeDasharray="2 3"
          />

          {/* Route Geodesic Arcs */}
          {ROUTES_DATA.map((route) => {
            const isHovered = route.id === activeRouteId;
            return (
              <g key={route.id} className="cursor-pointer" onClick={() => onSelectRoute?.(route.id)}>
                {/* Wider invisible path for easy hovering */}
                <path
                  d={route.pathD}
                  stroke="transparent"
                  strokeWidth={16}
                  fill="none"
                  onMouseEnter={() => setActiveRouteId(route.id)}
                />
                {/* Visible colored arc */}
                <path
                  d={route.pathD}
                  fill="none"
                  stroke={route.color}
                  strokeWidth={isHovered ? route.strokeWidth + 2 : route.strokeWidth}
                  strokeDasharray={route.dashArray}
                  strokeLinecap="round"
                  opacity={isHovered ? 1 : 0.8}
                  className="transition-all duration-200"
                  onMouseEnter={() => setActiveRouteId(route.id)}
                />
              </g>
            );
          })}

          {/* Flight Nodes (Metros) */}
          {METRO_NODES.map((node) => (
            <g key={node.code} transform={`translate(${node.x}, ${node.y})`}>
              <circle r="9" fill={node.color} fillOpacity="0.12" />
              <circle r="4" fill={node.color} stroke="#FFFFFF" strokeWidth="2" />
              <text
                x={node.labelX}
                y={node.labelY}
                className="text-[12px] font-bold font-mono fill-slate-800 select-none"
              >
                {node.code}
              </text>
              <text
                x={node.nameX}
                y={node.nameY}
                className="text-[9px] font-medium fill-slate-500 select-none"
              >
                {node.name}
              </text>
            </g>
          ))}
        </svg>

        {/* Floating Interactive Route Inspection Card */}
        <div className="absolute right-4 top-4 max-w-[260px] sm:max-w-xs bg-white/95 backdrop-blur-md rounded-xl border border-slate-200/90 shadow-lg p-4 space-y-2 text-left z-10 transition-all duration-200">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-1.5 font-mono text-sm font-bold text-slate-900">
              <span>{activeRoute.origin}</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              <span>{activeRoute.destination}</span>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono ${
                activeRoute.isPositive
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}
            >
              {activeRoute.percentShift}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block uppercase">Fare Shift</span>
              <span className="font-mono text-slate-800 font-semibold">{activeRoute.defaultFareShift}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block uppercase">Route Index</span>
              <span className={`font-mono font-bold ${activeRoute.isPositive ? 'text-emerald-600' : 'text-red-600'}`}>
                {activeRoute.defaultIndex}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block uppercase">Basket Weight</span>
              <span className="font-mono text-slate-600 font-medium">{activeRoute.defaultWeight}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block uppercase">Contribution</span>
              <span className={`font-mono font-bold ${activeRoute.isPositive ? 'text-emerald-600' : 'text-red-600'}`}>
                {activeRoute.contributionText}
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-500 font-medium truncate max-w-[175px]">
              {activeRoute.statusText}
            </span>
            {onSelectRoute && (
              <button
                type="button"
                onClick={() => onSelectRoute(activeRoute.id)}
                className="text-blue-600 hover:text-blue-800 font-semibold inline-flex items-center gap-0.5 ml-1 shrink-0 cursor-pointer"
              >
                <span>5A Math</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Legend Footer */}
      <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-2.5 h-1 bg-red-500 rounded"></span>
            Negative contribution
          </span>
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-2.5 h-1 bg-emerald-500 rounded"></span>
            Positive contribution
          </span>
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-2.5 h-1 bg-slate-300 rounded"></span>
            Baseline / Parity
          </span>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          Arc thickness scaled to DGCA basket weight $w_r^*$
        </span>
      </div>
    </div>
  );
};
