from django.core.management.base import BaseCommand
from core.models import Device, DeviceType, DeviceMode


class Command(BaseCommand):
    help = "Seed the database with sample devices"

    def handle(self, *args, **options):
        Device.objects.all().delete()
        self.stdout.write("Cleared existing devices")

        devices = [
            Device(
                name="Roof Solar Array",
                device_type=DeviceType.SOLAR_PANEL,
                properties={'rated_capacity_watts': 5000},
                current_state={'current_output_watts': 0}
            ),
            Device(
                name="Garage Solar Panels",
                device_type=DeviceType.SOLAR_PANEL,
                properties={'rated_capacity_watts': 2000},
                current_state={'current_output_watts': 0}
            ),
            Device(
                name="Powerwall",
                device_type=DeviceType.BATTERY,
                properties={
                    'capacity_wh': 13500,
                    'max_charge_rate_watts': 5000,
                    'max_discharge_rate_watts': 5000
                },
                current_state={
                    'current_charge_wh': 6750,
                    'mode': DeviceMode.IDLE,
                    'current_rate_watts': 0
                }
            ),
            Device(
                name="Tesla Model 3",
                device_type=DeviceType.ELECTRIC_VEHICLE,
                properties={
                    'battery_capacity_wh': 75000,
                    'max_charge_rate_watts': 11000,
                    'max_discharge_rate_watts': 7000
                },
                current_state={
                    'current_charge_wh': 60000,
                    'mode': DeviceMode.IDLE,
                    'current_rate_watts': 0
                }
            ),
            Device(
                name="HVAC System",
                device_type=DeviceType.APPLIANCE,
                properties={'average_power_draw_watts': 3000},
                current_state={'is_on': False, 'current_power_draw_watts': 0}
            ),
            Device(
                name="Dishwasher",
                device_type=DeviceType.APPLIANCE,
                properties={'average_power_draw_watts': 1800},
                current_state={'is_on': False, 'current_power_draw_watts': 0}
            ),
            Device(
                name="Water Heater",
                device_type=DeviceType.APPLIANCE,
                properties={'average_power_draw_watts': 4500},
                current_state={'is_on': False, 'current_power_draw_watts': 0}
            ),
            Device(
                name="Refrigerator",
                device_type=DeviceType.APPLIANCE,
                properties={'average_power_draw_watts': 150},
                current_state={'is_on': True, 'current_power_draw_watts': 150}
            ),
        ]

        Device.objects.bulk_create(devices)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {len(devices)} devices")
        )
