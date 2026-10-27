import React from 'react';
import { ExternalLink, History, RefreshCw, CheckCircle, XCircle, TrendingDown, Target } from 'lucide-react';
import { TrackedProduct } from '../types';

interface ProductCardProps {
  item: TrackedProduct;
  onViewHistory: (item: TrackedProduct) => void;
  onTriggerScrape: (productId: string) => void;
  isTriggering: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  item,
  onViewHistory,
  onTriggerScrape,
  isTriggering,
}) => {
  const product = item.product;
  const snapshot = item.latest_snapshot;
  const price = snapshot ? Number(snapshot.price) : null;
  const target = item.target_price ? Number(item.target_price) : null;

  return (
    <div className="glass-card rounded-2xl p-5 border border-slate-800/80 hover:border-slate-700/80 transition flex flex-col justify-between group">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700/60 truncate max-w-[150px]">
            {product.domain}
          </span>
          {snapshot && (
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${
                snapshot.in_stock
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              }`}
            >
              {snapshot.in_stock ? (
                <>
                  <CheckCircle className="w-3 h-3" /> In Stock
                </>
              ) : (
                <>
                  <XCircle className="w-3 h-3" /> Out of Stock
                </>
              )}
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="text-sm font-semibold text-white line-clamp-2 leading-snug group-hover:text-indigo-300 transition">
          {product.title}
        </h3>

        {/* Price Display */}
        <div className="mt-4 flex items-baseline justify-between">
          <div>
            <span className="text-xs text-slate-400 block mb-0.5">Current Price</span>
            {price !== null ? (
              <span className="text-2xl font-bold text-white tracking-tight">
                ${price.toFixed(2)}
                <span className="text-xs font-normal text-slate-400 ml-1">{snapshot?.currency || 'USD'}</span>
              </span>
            ) : (
              <span className="text-sm font-medium text-amber-400 italic">
                Extraction Pending
              </span>
            )}
          </div>

          {target !== null && (
            <div className="text-right">
              <span className="text-[11px] text-slate-400 flex items-center justify-end gap-1">
                <Target className="w-3 h-3 text-indigo-400" /> Target
              </span>
              <span className="text-sm font-semibold text-indigo-300">
                ${target.toFixed(2)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="mt-5 pt-4 border-t border-slate-800/60 flex items-center justify-between gap-2">
        <a
          href={product.canonical_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition"
          title="Open product page in new tab"
        >
          <span>Store Page</span>
          <ExternalLink className="w-3 h-3" />
        </a>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onTriggerScrape(product.id)}
            disabled={isTriggering}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition"
            title="Trigger scrape extraction now"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isTriggering ? 'animate-spin text-indigo-400' : ''}`} />
          </button>

          <button
            onClick={() => onViewHistory(item)}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-indigo-300 hover:bg-indigo-500/10 hover:text-indigo-200 border border-indigo-500/20 transition"
          >
            <History className="w-3.5 h-3.5" />
            <span>History</span>
          </button>
        </div>
      </div>
    </div>
  );
};
