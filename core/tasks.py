from celery import shared_task


# =============================================================================
# TODO: Implement telemetry simulation task
# =============================================================================
@shared_task
def simulate_telemetry():
    """
    Generate plausible energy values for each device type.
    Runs every minute (configured in config/celery.py).

    Requirements:
    - Solar output should vary by time of day (peak 10am-2pm)
    - Appliances should have realistic on/off patterns
    - Storage devices should update charge levels based on their mode
    """
    pass
