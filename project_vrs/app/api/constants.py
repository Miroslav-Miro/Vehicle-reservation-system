"""
Single source for reservation status names and small helper sets, used across the API (dashboards, filters and others)
"""

# Statuses seed in ReservationStatus.status
PENDING_PAYMENT = "PENDING_PAYMENT"  # waiting for payment confirmation
FAILED_PAYMENT = "FAILED_PAYMENT"  # payment failed
CONFIRMED = "CONFIRMED"  # payment is fine; reservation is confirmed
NO_SHOW = "NO_SHOW"  # customer didn't arrive on start date
ACTIVE = "ACTIVE"  # vehicle has been handed over to the customer
COMPLETED = "COMPLETED"  # vehicle returned; flow finished
CANCELLED = "CANCELLED"  # cancelled by user/manager/admin

# Sets the dashboard will use
ACTIVE_STATUSES = {
    PENDING_PAYMENT,
    CONFIRMED,
    ACTIVE,
}

FINAL_STATUSES = {
    COMPLETED,
    CANCELLED,
}

OPS_ALLOWED_ACTIONS = {
    # Payment gate:
    "PENDING_PAYMENT": ["CONFIRMED", "FAILED_PAYMENT", "CANCELLED"],
    # Start of rental:
    "CONFIRMED": ["ACTIVE", "NO_SHOW", "CANCELLED"],
    # If customer arrives late:
    "NO_SHOW": ["ACTIVE", "CANCELLED"],
    # During rental:
    "ACTIVE": ["COMPLETED"],
    # Retry or close if payment failed:
    "FAILED_PAYMENT": ["PENDING_PAYMENT", "CANCELLED"],
    COMPLETED: [],
    CANCELLED: [],
}
