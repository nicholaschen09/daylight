from dataclasses import dataclass
from core.models import Device, DeviceType, DeviceMode


@dataclass
class StorageState:
    """State of a storage device (Battery or EV)."""
    device_id: str
    device_name: str
    device_type: str
    capacity_wh: float
    current_charge_wh: float
    charge_percentage: float
    mode: str


@dataclass
class EnergySummary:
    """Snapshot of home energy status."""
    total_production_watts: float
    total_consumption_watts: float
    net_power_watts: float
    storage_states: list[StorageState]


class EnergyService:
    """Service for energy calculations and summaries."""

    @classmethod
    def get_energy_summary(cls) -> EnergySummary:
        """
        Calculate current energy summary across all active devices.

        Returns:
            EnergySummary with production, consumption, net flow, and storage states
        """
        devices = Device.objects.filter(is_active=True)

        total_production = 0.0
        total_consumption = 0.0
        storage_states = []

        for device in devices:
            power = device.current_power_watts

            if power > 0:
                total_production += power
            elif power < 0:
                total_consumption += abs(power)

            if device.device_type in [DeviceType.BATTERY, DeviceType.ELECTRIC_VEHICLE]:
                capacity = device.capacity_wh or 0
                current_charge = device.current_state.get('current_charge_wh', 0)

                storage_states.append(StorageState(
                    device_id=str(device.id),
                    device_name=device.name,
                    device_type=device.device_type,
                    capacity_wh=capacity,
                    current_charge_wh=current_charge,
                    charge_percentage=device.charge_percentage or 0,
                    mode=device.current_state.get('mode', DeviceMode.IDLE)
                ))

        net_power = total_production - total_consumption

        return EnergySummary(
            total_production_watts=total_production,
            total_consumption_watts=total_consumption,
            net_power_watts=net_power,
            storage_states=storage_states
        )
