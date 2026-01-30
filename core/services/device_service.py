from typing import Any
from django.db import transaction
from core.models import Device, DeviceType, DeviceMode


class DeviceValidationError(Exception):
    """Raised when device properties are invalid."""
    pass


class DeviceService:
    """Service for device registration and management."""

    REQUIRED_PROPERTIES = {
        DeviceType.SOLAR_PANEL: ['rated_capacity_watts'],
        DeviceType.BATTERY: ['capacity_wh', 'max_charge_rate_watts', 'max_discharge_rate_watts'],
        DeviceType.ELECTRIC_VEHICLE: ['battery_capacity_wh', 'max_charge_rate_watts', 'max_discharge_rate_watts'],
        DeviceType.APPLIANCE: ['average_power_draw_watts'],
    }

    @classmethod
    def validate_properties(cls, device_type: str, properties: dict) -> None:
        """Validate that required properties are present for device type."""
        required = cls.REQUIRED_PROPERTIES.get(device_type, [])
        missing = [prop for prop in required if prop not in properties]

        if missing:
            raise DeviceValidationError(
                f"Missing required properties for {device_type}: {missing}"
            )

        for key, value in properties.items():
            if isinstance(value, (int, float)) and value < 0:
                raise DeviceValidationError(
                    f"Property '{key}' must be non-negative, got {value}"
                )

    @classmethod
    def get_initial_state(cls, device_type: str, properties: dict) -> dict:
        """Generate initial current_state based on device type."""
        if device_type == DeviceType.SOLAR_PANEL:
            return {'current_output_watts': 0}

        if device_type == DeviceType.BATTERY:
            capacity = properties.get('capacity_wh', 0)
            return {
                'current_charge_wh': capacity * 0.5,
                'mode': DeviceMode.IDLE,
                'current_rate_watts': 0
            }

        if device_type == DeviceType.ELECTRIC_VEHICLE:
            capacity = properties.get('battery_capacity_wh', 0)
            return {
                'current_charge_wh': capacity * 0.8,
                'mode': DeviceMode.IDLE,
                'current_rate_watts': 0
            }

        if device_type == DeviceType.APPLIANCE:
            return {
                'is_on': False,
                'current_power_draw_watts': 0
            }

        return {}

    @classmethod
    @transaction.atomic
    def register_device(
        cls,
        name: str,
        device_type: str,
        properties: dict,
        description: str = ''
    ) -> Device:
        """
        Register a new device with validation.

        Args:
            name: Human-readable device name
            device_type: One of DeviceType choices
            properties: Type-specific properties dict
            description: Optional device description

        Returns:
            Created Device instance

        Raises:
            DeviceValidationError: If properties are invalid
        """
        cls.validate_properties(device_type, properties)

        initial_state = cls.get_initial_state(device_type, properties)

        device = Device.objects.create(
            name=name,
            description=description,
            device_type=device_type,
            properties=properties,
            current_state=initial_state
        )

        return device

    @classmethod
    def get_all_devices(
        cls,
        device_type: str = None,
        active_only: bool = True
    ) -> list[Device]:
        """Retrieve all devices, optionally filtered."""
        queryset = Device.objects.all()

        if active_only:
            queryset = queryset.filter(is_active=True)

        if device_type:
            queryset = queryset.filter(device_type=device_type)

        return list(queryset)

    @classmethod
    def get_device_by_id(cls, device_id: str) -> Device | None:
        """Retrieve a device by ID."""
        try:
            return Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            return None

    @classmethod
    def update_device_state(cls, device: Device, new_state: dict) -> Device:
        """Update device's current state."""
        device.current_state.update(new_state)
        device.save(update_fields=['current_state', 'updated_at'])
        return device

    @classmethod
    def set_storage_mode(
        cls,
        device: Device,
        mode: str,
        rate_watts: float = None
    ) -> Device:
        """
        Set operating mode for storage devices (Battery, EV).

        Args:
            device: Battery or EV device
            mode: One of DeviceMode choices
            rate_watts: Charge/discharge rate (uses max if not specified)

        Raises:
            DeviceValidationError: If device is not a storage device
        """
        if device.device_type not in [DeviceType.BATTERY, DeviceType.ELECTRIC_VEHICLE]:
            raise DeviceValidationError("Only storage devices have operating modes")

        if mode == DeviceMode.CHARGING:
            max_rate = device.properties.get('max_charge_rate_watts', 0)
        elif mode == DeviceMode.DISCHARGING:
            max_rate = device.properties.get('max_discharge_rate_watts', 0)
        else:
            max_rate = 0

        actual_rate = min(rate_watts, max_rate) if rate_watts else max_rate

        device.current_state['mode'] = mode
        device.current_state['current_rate_watts'] = actual_rate if mode != DeviceMode.IDLE else 0
        device.save(update_fields=['current_state', 'updated_at'])

        return device
