from celery import shared_task
from django.utils import timezone


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
    from core.models import Device
    from core.services import TelemetryService

    timestamp = timezone.now()
    devices = list(Device.objects.filter(is_active=True))

    for device in devices:
        new_state = TelemetryService.simulate_device(device, timestamp)
        device.current_state.update(new_state)

    # Bulk update for better performance at scale
    Device.objects.bulk_update(devices, ['current_state', 'updated_at'], batch_size=1000)

    # Record telemetry readings
    for device in devices:
        TelemetryService.record_telemetry(device, timestamp)

    return f"Simulated telemetry for {len(devices)} devices at {timestamp.isoformat()}"


@shared_task
def cleanup_old_telemetry(days_to_keep: int = 30):
    """
    Clean up telemetry readings older than specified days.

    For production, consider partitioning or TimescaleDB.
    """
    from datetime import timedelta
    from core.models import TelemetryReading

    cutoff = timezone.now() - timedelta(days=days_to_keep)
    deleted_count, _ = TelemetryReading.objects.filter(
        timestamp__lt=cutoff
    ).delete()

    return f"Deleted {deleted_count} old telemetry readings"
