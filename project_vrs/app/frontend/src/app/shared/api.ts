export function apiBase(): string {
  const w: any = (window as any) || {};
  const base: string | undefined = w.__env?.API_BASE;
  if (base && typeof base === 'string' && base.trim()) return base.replace(/\/$/, '');

  const host: string | undefined = w.__env?.API_HOST || localStorage.getItem('api_host') || undefined;
  if (host) {
    try {
      const u = new URL(/^https?:\/\//i.test(host) ? host : `https://${host}`);
      return `${u.origin.replace(/\/$/, '')}/api`;
    } catch {
      return `https://${String(host).replace(/\/$/, '')}/api`;
    }
  }

  // Fallback for local development
  return 'http://localhost:8000/api';
}

