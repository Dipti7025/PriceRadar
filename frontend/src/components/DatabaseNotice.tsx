import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, Copy, RefreshCw, X } from 'lucide-react';
import { DatabaseHealth } from '../types';

interface DatabaseNoticeProps {
  dbHealth?: DatabaseHealth;
  onRetry: () => void;
  isChecking: boolean;
}

export const DatabaseNotice: React.FC<DatabaseNoticeProps> = ({ dbHealth, onRetry, isChecking }) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [dismissed, setDismissed] = useState(false);

  if (dbHealth?.status === 'connected' || dismissed) {
    return null;
  }

  const commands = [
    { title: '1. Test Neon Database Connection', cmd: 'python verify_neon.py' },
    { title: '2. Apply Alembic Migrations to Neon', cmd: 'alembic upgrade head' },
    { title: '3. Start FastAPI Backend Server', cmd: 'python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000' },
  ];

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="mb-8 rounded-2xl border border-amber-500/30 bg-amber-950/20 p-5 backdrop-blur-md">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-amber-200">
              Backend API or Neon PostgreSQL Unreachable
            </h3>
            <p className="text-xs text-amber-300/80 mt-0.5">
              The frontend is unable to reach the FastAPI backend at <code className="text-amber-200">http://127.0.0.1:8000/health</code>.
              Ensure the backend is started and your Neon database migrations are applied.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRetry}
            disabled={isChecking}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/30 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isChecking ? 'animate-spin' : ''}`} />
            <span>Check Again</span>
          </button>
          <button
            onClick={() => setDismissed(true)}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800/50"
            title="Dismiss banner"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {dbHealth?.message && (
        <div className="mt-3 px-3 py-2 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] font-mono text-slate-400 break-all">
          <span className="text-amber-400 font-semibold">Diagnostic details:</span> {dbHealth.message}
        </div>
      )}

      {/* Copyable Quick Steps */}
      <div className="mt-4 grid gap-2.5 sm:grid-cols-3">
        {commands.map((c, i) => (
          <div key={i} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 flex flex-col justify-between">
            <span className="text-xs font-medium text-slate-300">{c.title}</span>
            <div className="mt-2 flex items-center justify-between gap-2 p-1.5 rounded bg-slate-950 font-mono text-[11px] text-indigo-300 border border-slate-800">
              <span className="truncate">{c.cmd}</span>
              <button
                onClick={() => handleCopy(c.cmd, i)}
                className="text-slate-400 hover:text-white shrink-0"
                title="Copy command"
              >
                {copiedIndex === i ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
