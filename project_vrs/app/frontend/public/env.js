// Runtime configuration injected before Angular bootstraps.
// Adjust values via deployment workflow without rebuilding the app.
// Example defaults for local development:
window.__env = Object.assign({}, window.__env || {}, {
  API_BASE: 'http://localhost:8000/api',
  API_HOST: 'localhost:8000'
});

