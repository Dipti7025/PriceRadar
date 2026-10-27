import React, { useEffect, useState, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { DatabaseNotice } from './components/DatabaseNotice';
import { StatsOverview } from './components/StatsOverview';
import { UrlSubmissionForm } from './components/UrlSubmissionForm';
import { ProductList } from './components/ProductList';
import { PriceHistoryModal } from './components/PriceHistoryModal';
import { AlertsDrawer } from './components/AlertsDrawer';
import { HealthStatus, TrackedProduct, AlertItem } from './types';
import { fetchHealth, fetchTrackedProducts, fetchAlerts, markAlertRead, triggerManualScrape } from './services/api';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [products, setProducts] = useState<TrackedProduct[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoadingProducts, setIsLoadingProducts] = useState(false);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState<TrackedProduct | null>(null);
  const [isAlertsOpen, setIsAlertsOpen] = useState(false);

  // Health check handler
  const loadHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch {
      // Degraded/unreachable state
      setHealth({
        status: 'degraded',
        service: 'PriceRadar Backend',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        components: {
          database: {
            status: 'disconnected',
            dialect: 'postgresql',
            message: 'Backend server is starting up or unreachable at http://127.0.0.1:8000',
          },
          system: {
            os: 'Windows',
            os_release: '',
            python_version: '3.13.12',
            environment: 'development',
          },
        },
      });
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  // Products loader
  const loadProducts = useCallback(async () => {
    setIsLoadingProducts(true);
    try {
      const data = await fetchTrackedProducts();
      setProducts(data);
    } catch {
      // Keep existing products or empty array
    } finally {
      setIsLoadingProducts(false);
    }
  }, []);

  // Alerts loader
  const loadAlerts = useCallback(async () => {
    try {
      const data = await fetchAlerts();
      setAlerts(data);
    } catch {
      // Ignored
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadHealth();
    loadProducts();
    loadAlerts();

    // Periodic gentle refresh every 30 seconds
    const interval = setInterval(() => {
      loadHealth();
      loadProducts();
      loadAlerts();
    }, 30000);

    return () => clearInterval(interval);
  }, [loadHealth, loadProducts, loadAlerts]);

  const handleTriggerScrape = async (productId: string) => {
    setTriggeringId(productId);
    try {
      await triggerManualScrape(productId);
      await loadProducts();
    } catch (e: any) {
      alert(`Scrape trigger notice: ${e.message}`);
    } finally {
      setTriggeringId(null);
    }
  };

  const handleMarkAlertRead = async (alertId: string) => {
    try {
      await markAlertRead(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a))
      );
    } catch (e) {
      console.error(e);
    }
  };

  const unreadAlertsCount = alerts.filter((a) => !a.is_read).length;
  const isDbConnected = health?.components?.database?.status === 'connected';

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Navigation */}
      <Navbar
        health={health}
        unreadAlertsCount={unreadAlertsCount}
        onOpenAlerts={() => setIsAlertsOpen(true)}
        onRefreshHealth={loadHealth}
        isCheckingHealth={isCheckingHealth}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Database Offline Notice Banner (if PostgreSQL isn't running) */}
        <DatabaseNotice
          dbHealth={health?.components?.database}
          onRetry={loadHealth}
          isChecking={isCheckingHealth}
        />

        {/* Dashboard Metric Tiles */}
        <StatsOverview
          totalTracked={products.length}
          totalAlerts={alerts.length}
          health={health}
        />

        {/* Product URL Submission Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-3">
            <UrlSubmissionForm
              onProductSubmitted={() => {
                loadProducts();
                loadAlerts();
              }}
              isDbConnected={isDbConnected}
            />
          </div>
        </div>

        {/* Tracked Products Feed */}
        <ProductList
          products={products}
          isLoading={isLoadingProducts}
          onRefresh={loadProducts}
          onViewHistory={(item) => setSelectedHistoryItem(item)}
          onTriggerScrape={handleTriggerScrape}
          triggeringId={triggeringId}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/90 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            PriceRadar &bull; Full-Stack Price Surveillance &bull; PostgreSQL 2.x &bull; FastAPI &bull; React
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>SSRF Guard: Active</span>
            <span>Robots.txt Policy: Strict Compliance</span>
          </div>
        </div>
      </footer>

      {/* Modals & Drawers */}
      <PriceHistoryModal
        item={selectedHistoryItem}
        onClose={() => setSelectedHistoryItem(null)}
      />

      <AlertsDrawer
        isOpen={isAlertsOpen}
        onClose={() => setIsAlertsOpen(false)}
        alerts={alerts}
        onMarkRead={handleMarkAlertRead}
      />
    </div>
  );
};

export default App;
