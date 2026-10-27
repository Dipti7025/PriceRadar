import React, { useEffect, useState } from 'react';
import { X, TrendingUp, TrendingDown, Clock, AlertCircle } from 'lucide-react';
import { TrackedProduct, PriceSnapshot } from '../types';
import { fetchPriceHistory } from '../services/api';

interface PriceHistoryModalProps {
  item: TrackedProduct | null;
  onClose: () => void;
}

export const PriceHistoryModal: React.FC<PriceHistoryModalProps> = ({ item, onClose }) => {
  const [snapshots, setSnapshots] = useState<PriceSnapshot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!item) return;
    setLoading(true);
    setError(null);
    fetchPriceHistory(item.product.id)
      .then((data) => setSnapshots(data))
      .catch((err) => setError(err.message || 'Failed to load price history'))
      .finally(() => setLoading(false));
  }, [item]);

  if (!item) return null;

  const prices = snapshots.map((s) => Number(s.price));
  const minPrice = prices.length ? Math.min(...prices) : null;
  const maxPrice = prices.length ? Math.max(...prices) : null;
  const latestPrice = prices.length ? prices[0] : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-2xl rounded-2xl glass-panel p-6 shadow-2xl border border-slate-700 max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div>
            <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400">
              Price History & Analytics
            </span>
            <h3 className="text-base font-semibold text-white mt-1 line-clamp-1">
              {item.product.title}
            </h3>
            <p className="text-xs text-slate-400 truncate mt-0.5">{item.product.domain}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Analytics Highlights */}
        {prices.length > 0 && (
          <div className="grid grid-cols-3 gap-3 my-4">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Lowest Recorded</span>
              <span className="text-sm font-bold text-emerald-400">${minPrice?.toFixed(2)}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Current Price</span>
              <span className="text-sm font-bold text-white">${latestPrice?.toFixed(2)}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Highest Recorded</span>
              <span className="text-sm font-bold text-slate-300">${maxPrice?.toFixed(2)}</span>
            </div>
          </div>
        )}

        {/* Snapshot list */}
        <div className="flex-1 overflow-y-auto pr-1 my-2 space-y-2">
          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400">Loading historical data...</div>
          ) : error ? (
            <div className="py-6 text-center text-xs text-rose-400">{error}</div>
          ) : snapshots.length === 0 ? (
            <div className="py-10 text-center text-xs text-slate-400 flex flex-col items-center">
              <Clock className="w-6 h-6 text-slate-500 mb-2" />
              <span>No price snapshots recorded yet. The background worker will populate prices shortly.</span>
            </div>
          ) : (
            snapshots.map((snap) => {
              const snapPrice = Number(snap.price);
              const isLowest = minPrice !== null && snapPrice === minPrice;
              return (
                <div
                  key={snap.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-slate-800 text-slate-300">
                      <Clock className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-white">
                        ${snapPrice.toFixed(2)} {snap.currency}
                        {isLowest && (
                          <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            All-time Low
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {new Date(snap.scraped_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-400">
                    {snap.in_stock ? (
                      <span className="text-emerald-400">In Stock</span>
                    ) : (
                      <span className="text-rose-400">Out of Stock</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
