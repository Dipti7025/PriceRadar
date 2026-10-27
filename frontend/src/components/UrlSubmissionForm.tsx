import React, { useState } from 'react';
import { PlusCircle, Link2, DollarSign, Mail, ShieldAlert, CheckCircle2, ArrowRight, Loader2, X } from 'lucide-react';
import { submitProduct, precheckUrlSsrf } from '../services/api';

interface UrlSubmissionFormProps {
  onProductSubmitted: () => void;
  isDbConnected: boolean;
}

export const UrlSubmissionForm: React.FC<UrlSubmissionFormProps> = ({ onProductSubmitted, isDbConnected }) => {
  const [url, setUrl] = useState('');
  const [targetPrice, setTargetPrice] = useState('');
  const [email, setEmail] = useState('');
  const [notifyOnDrop, setNotifyOnDrop] = useState(true);
  const [notifyOnTarget, setNotifyOnTarget] = useState(true);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Real-time client-side SSRF validation feedback
  const ssrfCheck = precheckUrlSsrf(url);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const cleanUrl = url.trim();
    if (!cleanUrl) {
      setError('Please provide a valid product page URL.');
      return;
    }

    if (!ssrfCheck.isSafe) {
      setError(`Cannot submit URL: ${ssrfCheck.warning}`);
      return;
    }

    setLoading(true);
    try {
      const res = await submitProduct({
        url: cleanUrl,
        target_price: targetPrice ? parseFloat(targetPrice) : null,
        user_email: email.trim() || null,
        notify_on_drop: notifyOnDrop,
        notify_on_target: notifyOnTarget,
      });

      setSuccess(`Product queued successfully! PriceRadar is now tracking: ${res.canonical_url}`);
      setUrl('');
      setTargetPrice('');
      
      // Trigger parent list refresh
      onProductSubmitted();
    } catch (err: any) {
      setError(err.message || 'Submission failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 shadow-xl border border-slate-800/80">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/60">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <PlusCircle className="w-5 h-5 text-indigo-400" />
            Track New Product
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Submit a public product page to track price movements with automatic SSRF inspection.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-5 space-y-4">
        {/* URL Input */}
        <div>
          <label htmlFor="product-url" className="block text-xs font-medium text-slate-300 mb-1.5">
            Product Page URL <span className="text-rose-400">*</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
              <Link2 className="w-4 h-4" />
            </div>
            <input
              id="product-url"
              type="text"
              required
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                if (error) setError(null);
              }}
              placeholder="https://example.com/item/wireless-headphones-pro"
              className={`w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 transition ${
                !ssrfCheck.isSafe && url.trim()
                  ? 'border-rose-500/60 focus:ring-rose-500/30'
                  : 'border-slate-700/80 focus:border-indigo-500 focus:ring-indigo-500/20'
              }`}
            />
          </div>

          {/* Real-time SSRF Warning */}
          {!ssrfCheck.isSafe && url.trim() && (
            <div className="mt-1.5 flex items-center gap-1.5 text-xs text-rose-400">
              <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
              <span>{ssrfCheck.warning}</span>
            </div>
          )}
        </div>

        {/* Target Price & Email Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="target-price" className="block text-xs font-medium text-slate-300 mb-1.5">
              Target Alert Price (Optional)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <DollarSign className="w-4 h-4" />
              </div>
              <input
                id="target-price"
                type="number"
                step="0.01"
                min="0"
                value={targetPrice}
                onChange={(e) => setTargetPrice(e.target.value)}
                placeholder="49.99"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700/80 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
              />
            </div>
          </div>

          <div>
            <label htmlFor="notification-email" className="block text-xs font-medium text-slate-300 mb-1.5">
              Notification Email (Optional)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <Mail className="w-4 h-4" />
              </div>
              <input
                id="notification-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="buyer@example.com"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700/80 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
              />
            </div>
          </div>
        </div>

        {/* Alert Toggles */}
        <div className="flex flex-wrap gap-4 pt-1">
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={notifyOnDrop}
              onChange={(e) => setNotifyOnDrop(e.target.checked)}
              className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-950"
            />
            <span>Alert on any price drop</span>
          </label>

          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={notifyOnTarget}
              onChange={(e) => setNotifyOnTarget(e.target.checked)}
              className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-950"
            />
            <span>Alert when target price is hit</span>
          </label>
        </div>

        {/* Status Messages */}
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start justify-between gap-2 animate-in fade-in">
            <div className="flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
              <span className="leading-relaxed">{error}</span>
            </div>
            <button
              type="button"
              onClick={() => setError(null)}
              className="p-1 rounded text-rose-400 hover:text-rose-200 hover:bg-rose-500/20 shrink-0"
              title="Dismiss error"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {success && (
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-start justify-between gap-2 animate-in fade-in">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" />
              <span className="leading-relaxed">{success}</span>
            </div>
            <button
              type="button"
              onClick={() => setSuccess(null)}
              className="p-1 rounded text-emerald-400 hover:text-emerald-200 hover:bg-emerald-500/20 shrink-0"
              title="Dismiss"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Submit Button */}
        <div className="pt-2 flex justify-end">
          <button
            id="submit-product-btn"
            type="submit"
            disabled={loading || (!ssrfCheck.isSafe && Boolean(url.trim()))}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 transition shadow-lg shadow-indigo-600/30 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Validating & Queuing...</span>
              </>
            ) : (
              <>
                <span>Start Tracking Price</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
