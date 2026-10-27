import React from 'react';
import { X, Bell, CheckCircle2, TrendingDown, Target, PackageX } from 'lucide-react';
import { AlertItem } from '../types';

interface AlertsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  alerts: AlertItem[];
  onMarkRead: (id: string) => void;
}

export const AlertsDrawer: React.FC<AlertsDrawerProps> = ({
  isOpen,
  onClose,
  alerts,
  onMarkRead,
}) => {
  if (!isOpen) return null;

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'PRICE_DROP':
        return <TrendingDown className="w-4 h-4 text-emerald-400" />;
      case 'TARGET_REACHED':
        return <Target className="w-4 h-4 text-indigo-400" />;
      case 'OUT_OF_STOCK':
        return <PackageX className="w-4 h-4 text-rose-400" />;
      default:
        return <Bell className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-slate-950 border-l border-slate-800 shadow-2xl p-6 flex flex-col justify-between">
          
          {/* Header */}
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-indigo-400" />
                <h2 className="text-base font-semibold text-white">Price Alerts & Notifications</h2>
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* List */}
            <div className="mt-4 space-y-3 max-h-[calc(100vh-160px)] overflow-y-auto pr-1">
              {alerts.length === 0 ? (
                <div className="py-16 text-center text-xs text-slate-400">
                  <Bell className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                  <span>No alerts triggered yet. You'll be notified here when prices change or meet your target.</span>
                </div>
              ) : (
                alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-xl border transition ${
                      alert.is_read
                        ? 'bg-slate-900/40 border-slate-800/60 opacity-75'
                        : 'bg-slate-900 border-indigo-500/30 shadow-lg shadow-indigo-950/40'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-lg bg-slate-800">
                          {getAlertIcon(alert.alert_type)}
                        </div>
                        <span className="text-xs font-semibold text-white">
                          {alert.alert_type.replace('_', ' ')}
                        </span>
                      </div>
                      {!alert.is_read && (
                        <button
                          onClick={() => onMarkRead(alert.id)}
                          className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium"
                        >
                          Mark read
                        </button>
                      )}
                    </div>

                    <p className="mt-2 text-xs text-slate-300 leading-relaxed">{alert.message}</p>

                    <div className="mt-2 text-[10px] text-slate-500">
                      {new Date(alert.triggered_at).toLocaleString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="pt-4 border-t border-slate-800">
            <button
              onClick={onClose}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-white transition"
            >
              Close
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};
