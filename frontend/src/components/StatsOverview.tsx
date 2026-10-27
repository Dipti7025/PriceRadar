import React from 'react';
import { Package, TrendingDown, BellRing, Activity } from 'lucide-react';
import { HealthStatus } from '../types';

interface StatsOverviewProps {
  totalTracked: number;
  totalAlerts: number;
  health: HealthStatus | null;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ totalTracked, totalAlerts, health }) => {
  const isDbConnected = health?.components?.database?.status === 'connected';

  const cards = [
    {
      label: 'Tracked Products',
      value: totalTracked,
      sub: 'Active URL monitors',
      icon: Package,
      color: 'indigo',
    },
    {
      label: 'Price Movements',
      value: 'Auto',
      sub: 'Evaluated on each extraction',
      icon: TrendingDown,
      color: 'emerald',
    },
    {
      label: 'Triggered Alerts',
      value: totalAlerts,
      sub: 'Drop & target price hits',
      icon: BellRing,
      color: 'amber',
    },
    {
      label: 'System & Database',
      value: isDbConnected ? 'PostgreSQL Active' : 'PostgreSQL Offline',
      sub: health?.version ? `Backend v${health.version}` : 'Connecting...',
      icon: Activity,
      color: isDbConnected ? 'emerald' : 'rose',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className="glass-card rounded-2xl p-4 sm:p-5 border border-slate-800/60 relative overflow-hidden group hover:border-slate-700/80 transition"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">{c.label}</span>
              <div
                className={`p-2 rounded-xl bg-slate-800/80 text-${c.color}-400 group-hover:scale-105 transition`}
              >
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-xl sm:text-2xl font-bold text-white tracking-tight">{c.value}</div>
              <div className="text-[11px] text-slate-500 mt-0.5">{c.sub}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
