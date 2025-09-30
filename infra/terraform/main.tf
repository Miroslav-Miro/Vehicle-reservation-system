locals {
  name         = lower(replace(var.project_name, "[^a-zA-Z0-9]", ""))
  acr_name     = substr("${local.name}acr", 0, 50)
  rg_name      = "${local.name}-rg"
  plan_name    = "${local.name}-plan"
  web_name     = "${local.name}-backend"
  worker_name  = "${local.name}-worker"
  redis_name   = substr("${local.name}-redis", 0, 63)
  pg_name      = substr("${local.name}-pg", 0, 60)
  swa_name     = "${local.name}-frontend"
}

resource "azurerm_resource_group" "rg" {
  name     = local.rg_name
  location = var.location
}

resource "azurerm_container_registry" "acr" {
  name                = local.acr_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = true
}

resource "azurerm_service_plan" "plan" {
  name                = local.plan_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_postgresql_flexible_server" "pg" {
  name                   = local.pg_name
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  administrator_login    = var.postgres_admin_username
  administrator_password = var.postgres_admin_password
  sku_name               = var.postgres_sku_name
  storage_mb             = 32768
  version                = "16"
  zone                   = "1"
  public_network_access_enabled = true
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_all" {
  name             = "allow-all"
  server_id        = azurerm_postgresql_flexible_server.pg.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}

resource "azurerm_postgresql_flexible_server_database" "db" {
  name      = var.sql_database_name
  server_id = azurerm_postgresql_flexible_server.pg.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_redis_cache" "redis" {
  name                = local.redis_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  capacity            = var.redis_capacity
  family              = "C"
  sku_name            = var.redis_sku_name
  enable_non_ssl_port = true
  minimum_tls_version = "1.2"
}

resource "azurerm_linux_web_app" "backend" {
  name                = local.web_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  https_only = true

  site_config {
    always_on         = true
    websockets_enabled = true

    application_stack {
      docker_image_name   = "${azurerm_container_registry.acr.login_server}/vrs-backend:${var.backend_image_tag}"
      docker_registry_url = azurerm_container_registry.acr.login_server
    }
  }

  app_settings = {
    WEBSITES_PORT                     = 8000
    DOCKER_REGISTRY_SERVER_URL        = "https://${azurerm_container_registry.acr.login_server}"
    DOCKER_REGISTRY_SERVER_USERNAME   = azurerm_container_registry.acr.admin_username
    DOCKER_REGISTRY_SERVER_PASSWORD   = azurerm_container_registry.acr.admin_password
    SECRET_KEY                        = var.django_secret_key
    DEBUG                             = var.debug ? "1" : "0"
    SQL_ENGINE                        = "django.db.backends.postgresql"
    SQL_DATABASE                      = azurerm_postgresql_flexible_server_database.db.name
    SQL_USER                          = var.postgres_admin_username
    SQL_PASSWORD                      = var.postgres_admin_password
    SQL_HOST                          = azurerm_postgresql_flexible_server.pg.fqdn
    SQL_PORT                          = 5432
    DATABASE                          = "postgres"
    REDIS_HOST                        = azurerm_redis_cache.redis.hostname
    REDIS_PORT                        = 6379
    CELERY_BROKER_URL                 = "redis://${azurerm_redis_cache.redis.hostname}:6379/0"
    CELERY_RESULT_BACKEND             = "django-db"
    ALLOWED_HOSTS                     = join(",", [azurerm_linux_web_app.backend.default_hostname, "localhost", "127.0.0.1"]) 
    CORS_ALLOWED_ORIGINS              = join(",", concat(var.cors_allowed_origins, ["https://${azurerm_static_site.frontend.default_hostname}"]))
    CSRF_TRUSTED_ORIGINS              = join(",", concat(var.cors_allowed_origins, ["https://${azurerm_static_site.frontend.default_hostname}"]))
  }
}

resource "azurerm_linux_web_app" "worker" {
  name                = local.worker_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  https_only = true

  site_config {
    always_on         = true
    application_stack {
      docker_image_name   = "${azurerm_container_registry.acr.login_server}/vrs-backend:${var.backend_image_tag}"
      docker_registry_url = azurerm_container_registry.acr.login_server
    }
    app_command_line = "sh -c 'celery -A backend worker -l info'"
  }

  app_settings = {
    WEBSITES_PORT                     = 8000
    DOCKER_REGISTRY_SERVER_URL        = "https://${azurerm_container_registry.acr.login_server}"
    DOCKER_REGISTRY_SERVER_USERNAME   = azurerm_container_registry.acr.admin_username
    DOCKER_REGISTRY_SERVER_PASSWORD   = azurerm_container_registry.acr.admin_password
    SECRET_KEY                        = var.django_secret_key
    DEBUG                             = var.debug ? "1" : "0"
    SQL_ENGINE                        = "django.db.backends.postgresql"
    SQL_DATABASE                      = azurerm_postgresql_flexible_server_database.db.name
    SQL_USER                          = var.postgres_admin_username
    SQL_PASSWORD                      = var.postgres_admin_password
    SQL_HOST                          = azurerm_postgresql_flexible_server.pg.fqdn
    SQL_PORT                          = 5432
    DATABASE                          = "postgres"
    REDIS_HOST                        = azurerm_redis_cache.redis.hostname
    REDIS_PORT                        = 6379
    CELERY_BROKER_URL                 = "redis://${azurerm_redis_cache.redis.hostname}:6379/0"
    CELERY_RESULT_BACKEND             = "django-db"
    ALLOWED_HOSTS                     = join(",", [azurerm_linux_web_app.worker.default_hostname, "localhost", "127.0.0.1"]) 
    CORS_ALLOWED_ORIGINS              = join(",", concat(var.cors_allowed_origins, ["https://${azurerm_static_site.frontend.default_hostname}"]))
    CSRF_TRUSTED_ORIGINS              = join(",", concat(var.cors_allowed_origins, ["https://${azurerm_static_site.frontend.default_hostname}"]))
  }
}

resource "azurerm_static_site" "frontend" {
  name                = local.swa_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku_tier            = "Free"
  sku_size            = "Free"
}

