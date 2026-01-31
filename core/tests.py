from django.test import TestCase
from core.models import Device, DeviceType, DeviceMode


class DeviceModelTest(TestCase):
    def setUp(self):
        self.solar = Device.objects.create(
            name="Test Solar Panel",
            device_type=DeviceType.SOLAR_PANEL,
            properties={"rated_capacity_watts": 5000},
            current_state={"current_output_watts": 2500},
        )
        self.battery = Device.objects.create(
            name="Test Battery",
            device_type=DeviceType.BATTERY,
            properties={
                "capacity_wh": 13500,
                "max_charge_rate_watts": 5000,
                "max_discharge_rate_watts": 5000,
            },
            current_state={
                "current_charge_wh": 6750,
                "mode": DeviceMode.IDLE,
                "current_rate_watts": 0,
            },
        )
        self.appliance = Device.objects.create(
            name="Test Appliance",
            device_type=DeviceType.APPLIANCE,
            properties={"average_power_draw_watts": 1500},
            current_state={"is_on": True, "current_power_draw_watts": 1500},
        )

    def test_solar_panel_is_producer(self):
        self.assertTrue(self.solar.is_producer)
        self.assertFalse(self.solar.is_consumer)

    def test_solar_panel_current_power(self):
        self.assertEqual(self.solar.current_power_watts, 2500)

    def test_solar_panel_not_producer_when_zero(self):
        self.solar.current_state["current_output_watts"] = 0
        self.assertFalse(self.solar.is_producer)

    def test_battery_charge_percentage(self):
        # 6750 / 13500 * 100 = 50%
        self.assertEqual(self.battery.charge_percentage, 50.0)

    def test_battery_discharging_is_producer(self):
        self.battery.current_state["mode"] = DeviceMode.DISCHARGING
        self.battery.current_state["current_rate_watts"] = 2000
        self.assertTrue(self.battery.is_producer)
        self.assertEqual(self.battery.current_power_watts, 2000)

    def test_battery_charging_is_consumer(self):
        self.battery.current_state["mode"] = DeviceMode.CHARGING
        self.battery.current_state["current_rate_watts"] = 2000
        self.assertTrue(self.battery.is_consumer)
        self.assertEqual(self.battery.current_power_watts, -2000)

    def test_appliance_is_consumer_when_on(self):
        self.assertTrue(self.appliance.is_consumer)
        self.assertEqual(self.appliance.current_power_watts, -1500)

    def test_appliance_not_consumer_when_off(self):
        self.appliance.current_state["is_on"] = False
        self.assertFalse(self.appliance.is_consumer)
        self.assertEqual(self.appliance.current_power_watts, 0)

    def test_capacity_wh_for_battery(self):
        self.assertEqual(self.battery.capacity_wh, 13500)

    def test_capacity_wh_for_solar_is_none(self):
        self.assertIsNone(self.solar.capacity_wh)
