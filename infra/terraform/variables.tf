variable "project_name" {
  type        = string
  description = "Project short name prefix (alphanumeric, 3-12 chars)."
}

variable "location" {
  type        = string
  default     = "westeurope"
  description = "Azure region."
}

variable "pg_location" {
  type        = string
  default     = ""
  description = "Optional override region for PostgreSQL Flexible Server. Leave empty to use var.location."
}

variable "backend_image_tag" {
  type        = string
  default     = "latest"
  description = "Container image tag for backend/worker. Overridden by CI on deploy."
}

variable "postgres_admin_username" {
  type        = string
  description = "PostgreSQL admin username."
}

variable "postgres_admin_password" {
  type        = string
  sensitive   = true
  description = "PostgreSQL admin password."
}

variable "sql_database_name" {
  type        = string
  default     = "vrsdb"
}

variable "postgres_sku_name" {
  type        = string
  default     = "B_Standard_B1ms"
  description = "SKU for PostgreSQL Flexible Server."
}

variable "redis_sku_name" {
  type        = string
  default     = "Basic"
  description = "Redis Cache SKU tier (Basic/Standard/Premium)."
}

variable "redis_capacity" {
  type        = number
  default     = 0
  description = "Redis Cache capacity (size within SKU family)."
}

variable "django_secret_key" {
  type        = string
  sensitive   = true
  description = "Django SECRET_KEY."
}

variable "debug" {
  type        = bool
  default     = false
}

variable "cors_allowed_origins" {
  type        = list(string)
  default     = []
  description = "Additional CORS origins (e.g., https://your-frontend)."
}
