import React from 'react';
import { PackageSearch, RefreshCw } from 'lucide-react';
import { TrackedProduct } from '../types';
import { ProductCard } from './ProductCard';

interface ProductListProps {
  products: TrackedProduct[];
  isLoading: boolean;
  onRefresh: () => void;
  onViewHistory: (item: TrackedProduct) => void;
  onTriggerScrape: (productId: string) => void;
  triggeringId: string | null;
}

export const ProductList: React.FC<ProductListProps> = ({
  products,
  isLoading,
  onRefresh,
  onViewHistory,
  onTriggerScrape,
  triggeringId,
}) => {
  return (
    <div className="mt-10">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Tracked Products</h2>
          <p className="text-xs text-slate-400 mt-0.5">Real-time price surveillance feed</p>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {isLoading && products.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-44 rounded-2xl bg-slate-900/40 border border-slate-800/40 animate-pulse" />
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-800 p-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-slate-400">
            <PackageSearch className="w-6 h-6" />
          </div>
          <h3 className="mt-4 text-sm font-semibold text-white">No products tracked yet</h3>
          <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
            Submit a product link above to begin monitoring price movements, stock updates, and target alerts.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((item) => (
            <ProductCard
              key={item.id}
              item={item}
              onViewHistory={onViewHistory}
              onTriggerScrape={onTriggerScrape}
              isTriggering={triggeringId === item.product.id}
            />
          ))}
        </div>
      )}
    </div>
  );
};
