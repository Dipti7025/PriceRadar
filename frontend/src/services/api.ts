import { HealthStatus, TrackedProduct, PriceSnapshot, AlertItem, ScrapeJobItem } from '../types';

/**
 * PriceRadar API Service
 * Directly targets the FastAPI backend at http://127.0.0.1:8000 by default.
 * Can be overridden with VITE_API_BASE_URL environment variable.
 */
export const BACKEND_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_BACKEND_URL ||
  'http://127.0.0.1:8000'
).replace(/\/+$/, '');

const API_BASE = `${BACKEND_URL}/api/v1`;

/**
 * Formats backend error responses (including Pydantic v2 validation arrays) into readable strings.
 */
export function formatApiError(body: any, status: number, fallback: string): string {
  if (body) {
    if (typeof body.detail === 'string') {
      return body.detail;
    }
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((err: any) => {
          const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : '';
          return field ? `${field}: ${err.msg}` : err.msg;
        })
        .join(' | ');
    }
    if (typeof body.message === 'string') {
      return body.message;
    }
  }

  if (status === 404) {
    return `Endpoint not found (404). Please verify FastAPI is running at ${BACKEND_URL}.`;
  }
  if (status === 503) {
    return 'Database or service temporarily unavailable (503).';
  }
  if (status === 500) {
    return 'Internal server error (500). Please check backend console logs.';
  }

  return fallback;
}

/**
 * Fetch system and database health status
 */
export async function fetchHealth(): Promise<HealthStatus> {
  const endpoints = [
    `${BACKEND_URL}/health`,
    `${BACKEND_URL}/api/v1/health`,
    '/health',
  ];

  let lastError: Error | null = null;
  for (const url of endpoints) {
    try {
      const res = await fetch(url, {
        headers: { 'Accept': 'application/json' },
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e: any) {
      lastError = e;
    }
  }

  throw lastError || new Error(`Backend unreachable at ${BACKEND_URL}`);
}

/**
 * Submit product URL for tracking with full error parsing and validation
 */
export async function submitProduct(data: {
  url: string;
  target_price?: number | null;
  user_email?: string | null;
  notify_on_drop?: boolean;
  notify_on_target?: boolean;
}): Promise<{ message: string; canonical_url: string; job_id?: string; product_id?: string }> {
  const endpoint = `${API_BASE}/products/submit`;

  let res: Response;
  try {
    res = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(data),
    });
  } catch (netErr: any) {
    throw new Error(
      `Cannot connect to PriceRadar backend at ${BACKEND_URL}. ` +
      `Ensure FastAPI is running with: python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
    );
  }

  let body: any = null;
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      body = await res.json();
    } catch {
      body = null;
    }
  }

  if (!res.ok) {
    const errorMsg = formatApiError(body, res.status, `Submission failed (HTTP ${res.status})`);
    throw new Error(errorMsg);
  }

  return body;
}

/**
 * Fetch all tracked products
 */
export async function fetchTrackedProducts(): Promise<TrackedProduct[]> {
  const endpoints = [
    `${API_BASE}/products/tracked`,
    '/api/v1/products/tracked',
  ];

  for (const url of endpoints) {
    try {
      const res = await fetch(url, {
        headers: { 'Accept': 'application/json' },
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // try next
    }
  }

  return [];
}

/**
 * Fetch historical price snapshots for a product
 */
export async function fetchPriceHistory(productId: string): Promise<PriceSnapshot[]> {
  const res = await fetch(`${API_BASE}/products/${productId}/history`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    let body: any = null;
    try { body = await res.json(); } catch {}
    throw new Error(formatApiError(body, res.status, 'Failed to fetch price history'));
  }
  return res.json();
}

/**
 * Fetch price alerts
 */
export async function fetchAlerts(unreadOnly = false): Promise<AlertItem[]> {
  try {
    const res = await fetch(`${API_BASE}/alerts/?unread_only=${unreadOnly}`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      return [];
    }
    return await res.json();
  } catch {
    return [];
  }
}

/**
 * Mark alert as read
 */
export async function markAlertRead(alertId: string): Promise<AlertItem> {
  const res = await fetch(`${API_BASE}/alerts/${alertId}/read`, {
    method: 'PATCH',
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    let body: any = null;
    try { body = await res.json(); } catch {}
    throw new Error(formatApiError(body, res.status, 'Failed to mark alert as read'));
  }
  return res.json();
}

/**
 * Trigger manual scrape extraction job
 */
export async function triggerManualScrape(productId: string): Promise<ScrapeJobItem> {
  const res = await fetch(`${API_BASE}/jobs/trigger/${productId}`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    let body: any = null;
    try { body = await res.json(); } catch {}
    throw new Error(formatApiError(body, res.status, 'Failed to trigger manual scrape'));
  }
  return res.json();
}

/**
 * Fetch scrape jobs
 */
export async function fetchScrapeJobs(): Promise<ScrapeJobItem[]> {
  try {
    const res = await fetch(`${API_BASE}/jobs/`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      return [];
    }
    return await res.json();
  } catch {
    return [];
  }
}

/**
 * Client-side preliminary SSRF check to provide instant UI feedback
 */
export function precheckUrlSsrf(inputUrl: string): { isSafe: boolean; warning?: string } {
  if (!inputUrl || inputUrl.trim() === '') {
    return { isSafe: true };
  }

  try {
    const url = new URL(inputUrl.trim());
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      return { isSafe: false, warning: `Unsafe protocol '${url.protocol}'. Only http: and https: are allowed.` };
    }

    const host = url.hostname.toLowerCase();
    if (
      host === 'localhost' ||
      host === '127.0.0.1' ||
      host === '::1' ||
      host.endsWith('.local') ||
      host.endsWith('.localhost') ||
      host.endsWith('.internal') ||
      host.startsWith('10.') ||
      host.startsWith('192.168.') ||
      host.startsWith('172.16.') ||
      host.startsWith('169.254.')
    ) {
      return { isSafe: false, warning: `SSRF Block: Internal or loopback destination (${host}) is strictly disallowed.` };
    }

    return { isSafe: true };
  } catch {
    return { isSafe: false, warning: 'Please enter a valid URL (e.g. https://store.example.com/item)' };
  }
}
