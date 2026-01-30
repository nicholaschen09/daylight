import math
import random
from datetime import datetime
from django.utils import timezone
from django.db.models import Avg, Max, Min
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth
from core.models import Device, DeviceType, DeviceMode, TelemetryReading


class TelemetryService:
    """Service for telemetry simulation and querying."""

    SOLAR_PEAK_HOUR = 12
    SOLAR_CURVE_WIDTH = 4

    APPLIANCE_ON_PROBABILITY = 0.3
    APPLIANCE_OFF_PROBABILITY = 0.2
    APPLIANCE_POWER_VARIANCE = 0.1

    @classmethod
    def calculate_solar_output(cls, device: Device, timestamp: datetime = None) -> float:
        """
        Calculate solar output based on time of day.

        Uses Gaussian curve centered at noon with peak during 10am-2pm.
        Returns 0 at night (before 6am, after 8pm).
        """
        if timestamp is None:
            timestamp = timezone.now()

        hour = timestamp.hour + timestamp.minute / 60.0

        if hour < 6 or hour > 20:
            return 0.0

        rated_capacity = device.properties.get('rated_capacity_watts', 0)

        exponent = -((hour - cls.SOLAR_PEAK_HOUR) ** 2) / (2 * cls.SOLAR_CURVE_WIDTH ** 2)
        base_output = rated_capacity * math.exp(exponent)

        variation = random.uniform(-0.15, 0.15)
        output = base_output * (1 + variation)

        return max(0, min(output, rated_capacity))

    @classmethod
    def simulate_appliance(cls, device: Device) -> tuple[bool, float]:
        """
        Simulate appliance on/off state and power draw.

        Returns:
            Tuple of (is_on, current_power_draw_watts)
        """
        current_on = device.current_state.get('is_on', False)
        avg_power = device.properties.get('average_power_draw_watts', 0)

        if current_on:
            is_on = random.random() > cls.APPLIANCE_OFF_PROBABILITY
        else:
            is_on = random.random() < cls.APPLIANCE_ON_PROBABILITY

        if is_on:
            variance = random.uniform(-cls.APPLIANCE_POWER_VARIANCE, cls.APPLIANCE_POWER_VARIANCE)
            power_draw = avg_power * (1 + variance)
        else:
            power_draw = 0.0

        return is_on, power_draw

    @classmethod
    def update_storage_charge(
        cls,
        device: Device,
        duration_seconds: float = 60
    ) -> float:
        """
        Update storage device charge level based on mode and rate.

        Args:
            device: Battery or EV device
            duration_seconds: Time period for charge update

        Returns:
            New charge level in Wh
        """
        mode = device.current_state.get('mode', DeviceMode.IDLE)
        rate_watts = device.current_state.get('current_rate_watts', 0)
        current_charge = device.current_state.get('current_charge_wh', 0)

        capacity = device.capacity_wh or 0

        energy_delta = (rate_watts * duration_seconds) / 3600

        if mode == DeviceMode.CHARGING:
            new_charge = current_charge + energy_delta
            new_charge = min(new_charge, capacity)
        elif mode == DeviceMode.DISCHARGING:
            new_charge = current_charge - energy_delta
            min_charge = capacity * 0.1
            new_charge = max(new_charge, min_charge)
        else:
            new_charge = current_charge

        return new_charge

    @classmethod
    def should_auto_idle(cls, device: Device, new_charge: float) -> bool:
        """Check if storage device should auto-switch to idle mode."""
        capacity = device.capacity_wh or 0
        mode = device.current_state.get('mode', DeviceMode.IDLE)

        if mode == DeviceMode.CHARGING and new_charge >= capacity:
            return True
        if mode == DeviceMode.DISCHARGING and new_charge <= capacity * 0.1:
            return True

        return False

    @classmethod
    def simulate_device(cls, device: Device, timestamp: datetime = None) -> dict:
        """
        Simulate telemetry for a single device.

        Returns:
            Updated state dict
        """
        if timestamp is None:
            timestamp = timezone.now()

        if device.device_type == DeviceType.SOLAR_PANEL:
            output = cls.calculate_solar_output(device, timestamp)
            return {'current_output_watts': output}

        if device.device_type == DeviceType.APPLIANCE:
            is_on, power_draw = cls.simulate_appliance(device)
            return {'is_on': is_on, 'current_power_draw_watts': power_draw}

        if device.device_type in [DeviceType.BATTERY, DeviceType.ELECTRIC_VEHICLE]:
            new_charge = cls.update_storage_charge(device)
            new_state = {
                **device.current_state,
                'current_charge_wh': new_charge
            }

            if cls.should_auto_idle(device, new_charge):
                new_state['mode'] = DeviceMode.IDLE
                new_state['current_rate_watts'] = 0

            return new_state

        return device.current_state

    @classmethod
    def record_telemetry(cls, device: Device, timestamp: datetime = None) -> TelemetryReading:
        """Create a telemetry reading for a device."""
        if timestamp is None:
            timestamp = timezone.now()

        power = device.current_power_watts
        charge = None

        if device.device_type in [DeviceType.BATTERY, DeviceType.ELECTRIC_VEHICLE]:
            charge = device.current_state.get('current_charge_wh')

        reading, _ = TelemetryReading.objects.update_or_create(
            device=device,
            timestamp=timestamp,
            defaults={
                'power_watts': power,
                'charge_wh': charge,
                'state_snapshot': device.current_state.copy()
            }
        )

        return reading

    @classmethod
    def get_telemetry_aggregated(
        cls,
        device: Device,
        start_time: datetime,
        end_time: datetime,
        interval: str = 'hour'
    ) -> list[dict]:
        """
        Get aggregated telemetry data over time range.

        Args:
            device: Device to query
            start_time: Start of range
            end_time: End of range
            interval: One of 'hour', 'day', 'week', 'month'

        Returns:
            List of aggregated readings
        """
        truncate_fn = {
            'hour': TruncHour,
            'day': TruncDay,
            'week': TruncWeek,
            'month': TruncMonth,
        }.get(interval, TruncHour)

        readings = TelemetryReading.objects.filter(
            device=device,
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).annotate(
            period=truncate_fn('timestamp')
        ).values('period').annotate(
            avg_power=Avg('power_watts'),
            max_power=Max('power_watts'),
            min_power=Min('power_watts'),
            avg_charge=Avg('charge_wh'),
        ).order_by('period')

        return list(readings)
