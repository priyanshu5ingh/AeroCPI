import React, { useState } from 'react';
import { Plane, Compass, ArrowRight, ExternalLink, Rotate3d, Layers, ShieldCheck, Info } from 'lucide-react';
import { DriverSummary } from '../types';
import { motion } from 'framer-motion';

interface SpatialRouteNetworkProps {
  drivers?: DriverSummary;
  onSelectRoute?: (routeId: string) => void;
}

interface AirportNode {
  code: string;
  name: string;
  x: number;
  y: number;
}

interface CorridorData {
  id: string;
  origin: string;
  destination: string;
  dgcaWeightPct: number;
  baseFare: number;
  currentFare: number;
  priceRelative: number;
  pointContrib: number;
  isSurge: boolean;
  elevationPx: number;
}

// Geographic airport coordinates mapped to a 600x650 viewport
const AIRPORTS: Record<string, AirportNode> = {
  DEL: { code: 'DEL', name: 'Delhi (IGI)', x: 260, y: 155 },
  BOM: { code: 'BOM', name: 'Mumbai (CSMIA)', x: 195, y: 320 },
  BLR: { code: 'BLR', name: 'Bengaluru (KIA)', x: 265, y: 445 },
  HYD: { code: 'HYD', name: 'Hyderabad (RGIA)', x: 285, y: 345 },
  MAA: { code: 'MAA', name: 'Chennai (MAA)', x: 315, y: 440 },
  CCU: { code: 'CCU', name: 'Kolkata (NSCBIA)', x: 445, y: 245 },
  GOI: { code: 'GOI', name: 'Goa (Dabolim)', x: 205, y: 395 },
  PAT: { code: 'PAT', name: 'Patna (JPIA)', x: 380, y: 205 },
  COK: { code: 'COK', name: 'Kochi (CIAL)', x: 235, y: 515 },
  PNQ: { code: 'PNQ', name: 'Pune (PNQ)', x: 220, y: 340 },
  AMD: { code: 'AMD', name: 'Ahmedabad (SVPIA)', x: 180, y: 250 },
};

// 10 DGCA sovereign basket corridors matching the frozen production run e1c05338-bc7a-4e2f-8b81-f855ca54c3be
const CORRIDORS: CorridorData[] = [
  { id: 'DEL-BOM', origin: 'DEL', destination: 'BOM', dgcaWeightPct: 17.8, baseFare: 6793, currentFare: 6792, priceRelative: 0.9999, pointContrib: -0.0026, isSurge: false, elevationPx: 38 },
  { id: 'BLR-DEL', origin: 'BLR', destination: 'DEL', dgcaWeightPct: 14.1, baseFare: 10289, currentFare: 9720, priceRelative: 0.9447, pointContrib: -0.7875, isSurge: false, elevationPx: 34 },
  { id: 'BLR-BOM', origin: 'BLR', destination: 'BOM', dgcaWeightPct: 11.6, baseFare: 7450, currentFare: 7549, priceRelative: 1.0133, pointContrib: +0.1499, isSurge: false, elevationPx: 30 },
  { id: 'DEL-HYD', origin: 'DEL', destination: 'HYD', dgcaWeightPct: 10.3, baseFare: 8825, currentFare: 9807, priceRelative: 1.1113, pointContrib: +1.0675, isSurge: true, elevationPx: 28 },
  { id: 'DEL-CCU', origin: 'DEL', destination: 'CCU', dgcaWeightPct: 9.9, baseFare: 8817, currentFare: 8817, priceRelative: 1.0000, pointContrib: 0.0000, isSurge: false, elevationPx: 26 },
  { id: 'MAA-DEL', origin: 'MAA', destination: 'DEL', dgcaWeightPct: 8.2, baseFare: 11260, currentFare: 10848, priceRelative: 0.9634, pointContrib: -0.2993, isSurge: false, elevationPx: 24 },
  { id: 'GOI-BOM', origin: 'GOI', destination: 'BOM', dgcaWeightPct: 8.0, baseFare: 9539, currentFare: 5230, priceRelative: 0.5483, pointContrib: -4.7391, isSurge: false, elevationPx: 23 },
  { id: 'BLR-HYD', origin: 'BLR', destination: 'HYD', dgcaWeightPct: 7.3, baseFare: 6427, currentFare: 6682.5, priceRelative: 1.0398, pointContrib: +0.2805, isSurge: false, elevationPx: 22 },
  { id: 'DEL-PAT', origin: 'DEL', destination: 'PAT', dgcaWeightPct: 6.6, baseFare: 6321, currentFare: 6531, priceRelative: 1.0332, pointContrib: +0.2125, isSurge: false, elevationPx: 20 },
  { id: 'BLR-CCU', origin: 'BLR', destination: 'CCU', dgcaWeightPct: 6.1, baseFare: 9062, currentFare: 9569, priceRelative: 1.0559, pointContrib: +0.3269, isSurge: false, elevationPx: 19 },
];

export const SpatialRouteNetwork: React.FC<SpatialRouteNetworkProps> = ({ drivers, onSelectRoute }) => {
  const [selectedRouteId, setSelectedRouteId] = useState<string>('DEL-HYD');

  const activeCorridor = CORRIDORS.find((c) => c.id === selectedRouteId) || CORRIDORS[0];

  const handleRouteClick = (routeId: string) => {
    setSelectedRouteId(routeId);
    if (onSelectRoute) {
      onSelectRoute(routeId);
    }
  };

  return (
    <div className="surface-solid p-6 sm:p-7 flex flex-col justify-between overflow-hidden relative">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2.5">
            <Compass className="w-5 h-5 text-blue-600 shrink-0" />
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Sovereign Route Basket Network
            </h2>
            <span className="text-[11px] font-mono font-bold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200/80 uppercase">
              10 DGCA Corridors
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Corridor flight arc elevation and prominence are mathematically mapped to official DGCA passenger volume weights ($w_r$).
          </p>
        </div>


      </div>

      {/* Main Map & Inspection Split Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center pt-4">
        {/* Geographic Network Canvas (SVG / Spatial Arc) */}
        <div className="lg:col-span-7 flex items-center justify-center relative min-h-[420px] bg-slate-50/50 rounded-2xl border border-slate-100 p-2">
          {/* Subtle Geographic Background Silhouette */}
          <svg
            viewBox="100 80 400 480"
            className="w-full max-h-[440px] select-none"
          >
            <defs>
              {/* Active Route Glow Filter */}
              <filter id="routeGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#1D4ED8" floodOpacity="0.3" />
              </filter>
            </defs>

            {/* India Continental Coastline & Border Guide Lines */}
            <path
              d="M 230 110 L 260 145 L 300 135 L 340 180 L 400 200 L 445 245 L 390 280 L 325 360 L 315 440 L 280 520 L 255 540 L 235 515 L 205 395 L 195 320 L 175 260 L 180 210 Z"
              fill="#FFFFFF"
              stroke="#E2E8F0"
              strokeWidth="1.5"
              strokeDasharray="4 4"
              opacity="0.9"
            />

            {/* Render 10 DGCA Flight Corridor Arcs */}
            {CORRIDORS.map((c) => {
              const orig = AIRPORTS[c.origin];
              const dest = AIRPORTS[c.destination];
              if (!orig || !dest) return null;

              const isSelected = c.id === selectedRouteId;
              const opacity = selectedRouteId ? (isSelected ? 1.0 : 0.22) : 0.85;

              // Quadratic Bezier Arc camber calculation
              const midX = (orig.x + dest.x) / 2;
              const midY = (orig.y + dest.y) / 2;
              const dx = dest.x - orig.x;
              const dy = dest.y - orig.y;
              const dist = Math.sqrt(dx * dx + dy * dy);

              // In spatial mode, elevation camber is amplified proportional to DGCA weight
              const camberFactor = (c.elevationPx / 20) * 0.28;
              const perpX = -dy / dist * dist * camberFactor;
              const perpY = dx / dist * dist * camberFactor;
              const ctrlX = midX + perpX;
              const ctrlY = midY + perpY;

              const strokeColor = c.isSurge
                ? (isSelected ? '#DC2626' : '#EF4444')
                : (isSelected ? '#059669' : '#10B981');

              const strokeWidth = isSelected
                ? Math.max(3.8, c.dgcaWeightPct / 3.2)
                : Math.max(2.2, c.dgcaWeightPct / 5.2);

              return (
                <g key={c.id} className="cursor-pointer transition-opacity duration-300" onClick={() => handleRouteClick(c.id)}>
                  {/* Invisible wide stroke hit-box for easier clicking */}
                  <path
                    d={`M ${orig.x} ${orig.y} Q ${ctrlX} ${ctrlY} ${dest.x} ${dest.y}`}
                    stroke="transparent"
                    strokeWidth="18"
                    fill="none"
                  />
                  {/* Visual Corridor Arc */}
                  <path
                    d={`M ${orig.x} ${orig.y} Q ${ctrlX} ${ctrlY} ${dest.x} ${dest.y}`}
                    stroke={strokeColor}
                    strokeWidth={strokeWidth}
                    fill="none"
                    strokeLinecap="round"
                    opacity={opacity}
                    filter={isSelected ? 'url(#routeGlow)' : undefined}
                  />
                </g>
              );
            })}

            {/* Render Airport Nodes */}
            {Object.values(AIRPORTS).map((apt) => {
              const isAttached = activeCorridor.origin === apt.code || activeCorridor.destination === apt.code;
              return (
                <g key={apt.code} className="select-none">
                  {/* Node Halo */}
                  {isAttached && (
                    <circle cx={apt.x} cy={apt.y} r="10" fill="#2563EB" fillOpacity="0.18" />
                  )}
                  {/* Outer Ring */}
                  <circle
                    cx={apt.x}
                    cy={apt.y}
                    r={isAttached ? '5.5' : '3.5'}
                    fill="#FFFFFF"
                    stroke={isAttached ? '#1D4ED8' : '#94A3B8'}
                    strokeWidth="2"
                  />
                  {/* Node Label */}
                  <text
                    x={apt.x + 8}
                    y={apt.y + 3}
                    className={`text-[10px] font-mono font-bold ${
                      isAttached ? 'fill-blue-900 font-extrabold' : 'fill-slate-500'
                    }`}
                  >
                    {apt.code}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Corridor Inspection Detail Panel (Surface Elevated) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="surface-elevated p-5 sm:p-6 space-y-4">
            {/* Header: Selected Corridor & Direction */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-extrabold font-mono text-slate-900">
                    {activeCorridor.origin}
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-400" />
                  <span className="text-xl font-extrabold font-mono text-slate-900">
                    {activeCorridor.destination}
                  </span>
                </div>
                <span className="text-xs text-slate-500 font-medium">
                  {AIRPORTS[activeCorridor.origin]?.name} → {AIRPORTS[activeCorridor.destination]?.name}
                </span>
              </div>

              <div
                className={`px-2.5 py-1 rounded-xl text-xs font-mono font-bold border ${
                  activeCorridor.isSurge
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                }`}
              >
                {activeCorridor.pointContrib > 0 ? `+${activeCorridor.pointContrib.toFixed(2)}` : activeCorridor.pointContrib.toFixed(2)} index shift
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="surface-subtle p-3 space-y-1">
                <span className="text-slate-500 font-medium block">DGCA Basket Weight</span>
                <span className="text-base font-bold font-mono text-slate-900 block">
                  {activeCorridor.dgcaWeightPct}%
                </span>
                <span className="text-[10px] text-slate-400">Quarterly Passenger Flow</span>
              </div>

              <div className="surface-subtle p-3 space-y-1">
                <span className="text-slate-500 font-medium block">Jevons Price Relative</span>
                <span className="text-base font-bold font-mono text-slate-900 block">
                  {activeCorridor.priceRelative.toFixed(3)}
                </span>
                <span className="text-[10px] text-slate-400">Current / Base Fare</span>
              </div>
            </div>

            {/* Representative Fare Comparison */}
            <div className="surface-subtle p-3 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Matched Base Fare (P₀)</span>
                <span className="font-mono font-bold text-slate-700">₹{activeCorridor.baseFare.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Current Fare (Pₜ)</span>
                <span className="font-mono font-bold text-slate-900">₹{activeCorridor.currentFare.toLocaleString()}</span>
              </div>
              <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Log-Linear Contribution (Cᵣ)</span>
                <span className={`font-mono font-bold ${activeCorridor.pointContrib > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                  {activeCorridor.pointContrib > 0 ? `+${activeCorridor.pointContrib.toFixed(2)}` : activeCorridor.pointContrib.toFixed(2)} contribution
                </span>
              </div>
            </div>

            {/* Inspect Button */}
            <button
              type="button"
              data-testid={`inspect-corridor-${activeCorridor.id}`}
              onClick={() => handleRouteClick(activeCorridor.id)}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-blue-50/90 text-blue-700 hover:bg-blue-100/90 border border-blue-200/90 text-xs font-bold transition-all cursor-pointer"
            >
              <span>Inspect Level 2 Attribution Math</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Quick Route Selector Chips */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {CORRIDORS.map((c) => (
              <button
                type="button"
                key={c.id}
                onClick={() => setSelectedRouteId(c.id)}
                className={`px-2.5 py-1 rounded-lg font-mono text-[11px] font-bold transition-all cursor-pointer ${
                  c.id === selectedRouteId
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}
              >
                {c.origin}→{c.destination}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
