Azure automated deployment (Terraform + GitHub Actions)

What this sets up
- Terraform to provision Azure resources: ACR, App Service Plan, Web Apps (backend + Celery worker), PostgreSQL Flexible Server, Redis Cache, Static Web App (SWA).
- GitHub Actions to:
  - provision: run Terraform apply on demand
  - deploy: build/push Docker image for backend, update Web App images, deploy Angular to SWA, and write runtime API URL to env.js

Prerequisites
- Azure Subscription
- A Service Principal with contributor rights to the subscription
- GitHub repository secrets configured

GitHub Secrets to add
- AZURE_CREDENTIALS: JSON from `az ad sp create-for-rbac --name vrs-sp --role contributor --scopes /subscriptions/<subId> --sdk-auth`
- PROJECT_NAME: short name (e.g., `vrsdemo`)
- POSTGRES_ADMIN_USERNAME
- POSTGRES_ADMIN_PASSWORD
- DJANGO_SECRET_KEY
- ACR_NAME: will be `<project_name>acr` (from Terraform output if customized)
- RESOURCE_GROUP: will be `<project_name>-rg` (from Terraform output)
- BACKEND_WEBAPP_NAME: `<project_name>-backend`
- WORKER_WEBAPP_NAME: `<project_name>-worker`
- ACR_USERNAME and ACR_PASSWORD: from `az acr credential show -n <ACR_NAME>` (or use admin creds from Terraform output)
- AZURE_STATIC_WEB_APPS_API_TOKEN: from Terraform output `static_site_deployment_token`

Optional GitHub Variables
- AZURE_LOCATION (default westeurope)
- SQL_DATABASE_NAME (default vrsdb)

First-time setup
1) Run the Provision workflow: GitHub Actions > `provision-infra` > Run workflow.
2) Copy the `static_site_deployment_token` output into the repo secret `AZURE_STATIC_WEB_APPS_API_TOKEN`.
3) Set ACR credentials/secrets as above.
4) Push to `main` (or re-run Deploy workflow) to deploy backend + frontend.

Notes
- The backend image tag is the git SHA; Terraform keeps infra static while the Deploy workflow updates image tags.
- WebSockets are enabled on the backend Web App; Channels uses Redis (non-SSL port enabled for simplicity).
- Angular reads runtime API config from `public/env.js`; the Deploy workflow rewrites it to the backend hostname.
- For production hardening: restrict Postgres firewall, disable Redis non-SSL port and add TLS support in Django Channels config, add custom domains + HTTPS.

