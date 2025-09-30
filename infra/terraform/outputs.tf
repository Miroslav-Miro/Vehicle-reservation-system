output "resource_group" {
  value = azurerm_resource_group.rg.name
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "acr_name" {
  value = azurerm_container_registry.acr.name
}

output "backend_webapp_name" {
  value = azurerm_linux_web_app.backend.name
}

output "backend_hostname" {
  value = azurerm_linux_web_app.backend.default_hostname
}

output "worker_webapp_name" {
  value = azurerm_linux_web_app.worker.name
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.pg.fqdn
}

output "redis_hostname" {
  value = azurerm_redis_cache.redis.hostname
}

output "static_site_name" {
  value = azurerm_static_site.frontend.name
}

output "static_site_hostname" {
  value = azurerm_static_site.frontend.default_host_name
}

output "static_site_deployment_token" {
  value     = azurerm_static_site.frontend.api_key
  sensitive = true
}
