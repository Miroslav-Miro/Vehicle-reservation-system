Terraform for Azure provisioning

Resources
- Resource Group
- Azure Container Registry (ACR)
- App Service Plan (Linux)
- Linux Web Apps: backend (Django ASGI) and worker (Celery)
- Azure Database for PostgreSQL Flexible Server + Database
- Azure Cache for Redis
- Azure Static Web App (SWA)

Usage
1) Ensure you have an Azure subscription and a Service Principal with appropriate permissions.
2) Export/define the following Terraform variables via CLI flags or a .tfvars file:

   - project_name
   - postgres_admin_username
   - postgres_admin_password
   - django_secret_key
   - optional: location, sql_database_name, backend_image_tag, cors_allowed_origins

3) Run:

   terraform init
   terraform plan -var 'project_name=yourproj' -var 'postgres_admin_username=pgadmin' -var 'postgres_admin_password=<<secret>>' -var 'django_secret_key=<<secret>>'
   terraform apply -auto-approve -var 'project_name=yourproj' -var 'postgres_admin_username=pgadmin' -var 'postgres_admin_password=<<secret>>' -var 'django_secret_key=<<secret>>'

Outputs
- ACR name and login server
- Web app names/hostnames
- Postgres FQDN, Redis host
- Static Web App name/hostname and deployment token (use as GitHub secret AZURE_STATIC_WEB_APPS_API_TOKEN)

Notes
- ACR admin is enabled for simplicity; Web Apps use registry credentials from app settings.
- Redis non-SSL port is enabled to match current Channels/Celery config.
- Firewall rule allows public access to Postgres for simplicity; tighten for production.

