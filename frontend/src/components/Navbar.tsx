import React from 'react';
import { Radar, Database, Bell, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';
import { HealthStatus } from '../types';

interface NavbarProps {
  health: HealthStatus | null;
  unreadAlertsCount: number;
  onOpenAlerts: () => void;
  onRefreshHealth: () => void;
  isCheckingHealth: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  unreadAlertsCount,
  onOpenAlerts,
  onRefreshHealth,
  isCheckingHealth,
}) => {
  const isDbConnected = health?.components?.database?.status === 'connected';

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/25">
            <Radar className="w-5 h-5 text-white animate-spin-slow" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-white">Price<span className="text-indigo-400">Radar</span></span>
              <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Intelligent Price Tracking & SSRF Guard</p>
          </div>
        </div>

        {/* Center / Right Status & Actions */}
        <div className="flex items-center gap-3 sm:gap-4">
          
          {/* PostgreSQL Status Indicator */}
          <button
            id="status-postgres-btn"
            onClick={onRefreshHealth}
            title={isDbConnected ? 'PostgreSQL is connected and active' : 'PostgreSQL is disconnected. Click to recheck.'}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              isDbConnected
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20 animate-pulse'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span className="hidden md:inline">PostgreSQL:</span>
            <span>{isDbConnected ? 'Connected' : 'Offline'}</span>
            <RefreshCw className={`w-3 h-3 text-slate-400 ${isCheckingHealth ? 'animate-spin' : ''}`} />
          </button>

          {/* SSRF Guard Badge */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>SSRF Protected</span>
          </div>

          {/* Alerts Trigger Button */}
          <button
            id="nav-alerts-btn"
            onClick={onOpenAlerts}
            className="relative p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition"
            aria-label="View notifications and alerts"
          >
            <Bell className="w-5 h-5" />
            {unreadAlertsCount > 0 && (
              <span className="absolute -top-1 -right-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-rose-500 text-white shadow-sm shadow-rose-500/50">
                {unreadAlertsCount}
              </span>
            )}
          </button>

        </div>
      </div>
    </header>
  );
};
