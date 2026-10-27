export interface DatabaseHealth {
  status: 'connected' | 'disconnected' | 'degraded';
  dialect: string;
  host?: string;
  port?: number;
  database?: string;
  message: string;
}

export interface SystemHealth {
  os: string;
  os_release: string;
  python_version: string;
  environment: string;
}

export interface HealthStatus {
  status: 'ok' | 'degraded';
  service: string;
  version: string;
  timestamp: string;
  components: {
    database: DatabaseHealth;
    system: SystemHealth;
  };
}

export interface Product {
  id: string;
  canonical_url: string;
  domain: string;
  title: string;
  description?: string | null;
  image_url?: string | null;
  sku?: string | null;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface PriceSnapshot {
  id: string;
  product_id: string;
  price: number | string;
  original_price?: number | string | null;
  currency: string;
  in_stock: boolean;
  seller?: string | null;
  scraped_at: string;
}

export interface TrackedProduct {
  id: string;
  product_id: string;
  product: Product;
  user_email?: string | null;
  target_price?: number | string | null;
  is_active: boolean;
  notify_on_drop: boolean;
  notify_on_target: boolean;
  created_at: string;
  updated_at: string;
  latest_snapshot?: PriceSnapshot | null;
  price_change_amount?: number | null;
  price_change_percent?: number | null;
}

export interface AlertItem {
  id: string;
  tracked_product_id: string;
  alert_type: 'PRICE_DROP' | 'TARGET_REACHED' | 'OUT_OF_STOCK' | 'BACK_IN_STOCK';
  threshold_price?: number | string | null;
  triggered_price: number | string;
  message: string;
  is_read: boolean;
  triggered_at: string;
}

export interface ScrapeJobItem {
  id: string;
  product_id?: string | null;
  url: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  error_message?: string | null;
  retry_count: number;
  scheduled_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}
