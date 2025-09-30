// Runtime configuration injected before Angular bootstraps.
// Adjust values via deployment workflow without rebuilding the app.
// Example defaults for local development:
window.__env = Object.assign({}, window.__env || {}, {
  API_BASE: 'https://vrs-backend-8923.azurewebsites.net/api',
  API_HOST: 'vrs-backend-8923.azurewebsites.net'
});

