import graphene
from graphene_django import DjangoObjectType
from core.models import Device, DeviceType, TelemetryReading
from core.services import DeviceService, EnergyService, DeviceValidationError


class DeviceTypeEnum(graphene.Enum):
    """GraphQL enum for device types."""
    SOLAR_PANEL = 'solar_panel'
    BATTERY = 'battery'
    ELECTRIC_VEHICLE = 'electric_vehicle'
    APPLIANCE = 'appliance'


class DeviceModeEnum(graphene.Enum):
    """GraphQL enum for storage device modes."""
    CHARGING = 'charging'
    DISCHARGING = 'discharging'
    IDLE = 'idle'


class DeviceNode(DjangoObjectType):
    """GraphQL type for Device model."""

    class Meta:
        model = Device
        fields = [
            'id', 'name', 'description', 'device_type', 'is_active',
            'properties', 'current_state', 'created_at', 'updated_at'
        ]

    current_power_watts = graphene.Float()
    charge_percentage = graphene.Float()
    is_producing = graphene.Boolean()
    is_consuming = graphene.Boolean()

    def resolve_current_power_watts(self, info):
        return self.current_power_watts

    def resolve_charge_percentage(self, info):
        return self.charge_percentage

    def resolve_is_producing(self, info):
        return self.is_producer

    def resolve_is_consuming(self, info):
        return self.is_consumer


class StorageStateType(graphene.ObjectType):
    """GraphQL type for storage device state in energy summary."""
    device_id = graphene.ID()
    device_name = graphene.String()
    device_type = graphene.String()
    capacity_wh = graphene.Float()
    current_charge_wh = graphene.Float()
    charge_percentage = graphene.Float()
    mode = graphene.String()


class EnergySummaryType(graphene.ObjectType):
    """GraphQL type for energy summary."""
    total_production_watts = graphene.Float()
    total_consumption_watts = graphene.Float()
    net_power_watts = graphene.Float()
    storage_states = graphene.List(StorageStateType)


class TelemetryReadingNode(DjangoObjectType):
    """GraphQL type for telemetry readings."""

    class Meta:
        model = TelemetryReading
        fields = ['id', 'timestamp', 'power_watts', 'charge_wh', 'state_snapshot']


class SolarPanelPropertiesInput(graphene.InputObjectType):
    """Input for solar panel properties."""
    rated_capacity_watts = graphene.Int(required=True)


class BatteryPropertiesInput(graphene.InputObjectType):
    """Input for battery properties."""
    capacity_wh = graphene.Int(required=True)
    max_charge_rate_watts = graphene.Int(required=True)
    max_discharge_rate_watts = graphene.Int(required=True)


class EVPropertiesInput(graphene.InputObjectType):
    """Input for electric vehicle properties."""
    battery_capacity_wh = graphene.Int(required=True)
    max_charge_rate_watts = graphene.Int(required=True)
    max_discharge_rate_watts = graphene.Int(required=True)


class AppliancePropertiesInput(graphene.InputObjectType):
    """Input for appliance properties."""
    average_power_draw_watts = graphene.Int(required=True)


class DevicePropertiesInput(graphene.InputObjectType):
    """
    Union-like input for device properties.
    Only one should be provided based on device_type.
    """
    solar_panel = graphene.Field(SolarPanelPropertiesInput)
    battery = graphene.Field(BatteryPropertiesInput)
    electric_vehicle = graphene.Field(EVPropertiesInput)
    appliance = graphene.Field(AppliancePropertiesInput)


class RegisterDeviceInput(graphene.InputObjectType):
    """Input for registering a new device."""
    name = graphene.String(required=True)
    description = graphene.String()
    device_type = DeviceTypeEnum(required=True)
    properties = graphene.Field(DevicePropertiesInput, required=True)


class RegisterDevice(graphene.Mutation):
    """Mutation to register a new device."""

    class Arguments:
        input = RegisterDeviceInput(required=True)

    device = graphene.Field(DeviceNode)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        try:
            device_type = input.device_type
            properties_input = input.properties

            # Convert enum to string for comparison
            device_type_str = device_type if isinstance(device_type, str) else device_type.value

            # Extract properties based on device type
            properties = None
            if device_type_str == DeviceType.SOLAR_PANEL and properties_input.solar_panel:
                properties = {
                    'rated_capacity_watts': properties_input.solar_panel.rated_capacity_watts
                }
            elif device_type_str == DeviceType.BATTERY and properties_input.battery:
                properties = {
                    'capacity_wh': properties_input.battery.capacity_wh,
                    'max_charge_rate_watts': properties_input.battery.max_charge_rate_watts,
                    'max_discharge_rate_watts': properties_input.battery.max_discharge_rate_watts,
                }
            elif device_type_str == DeviceType.ELECTRIC_VEHICLE and properties_input.electric_vehicle:
                properties = {
                    'battery_capacity_wh': properties_input.electric_vehicle.battery_capacity_wh,
                    'max_charge_rate_watts': properties_input.electric_vehicle.max_charge_rate_watts,
                    'max_discharge_rate_watts': properties_input.electric_vehicle.max_discharge_rate_watts,
                }
            elif device_type_str == DeviceType.APPLIANCE and properties_input.appliance:
                properties = {
                    'average_power_draw_watts': properties_input.appliance.average_power_draw_watts
                }

            if not properties:
                return RegisterDevice(
                    device=None,
                    success=False,
                    errors=[f"Properties required for device type: {device_type_str}"]
                )

            device = DeviceService.register_device(
                name=input.name,
                description=input.description or '',
                device_type=device_type_str,
                properties=properties
            )

            return RegisterDevice(device=device, success=True, errors=[])

        except DeviceValidationError as e:
            return RegisterDevice(device=None, success=False, errors=[str(e)])
        except Exception as e:
            return RegisterDevice(device=None, success=False, errors=[str(e)])


class SetStorageMode(graphene.Mutation):
    """Mutation to set operating mode for storage devices."""

    class Arguments:
        device_id = graphene.ID(required=True)
        mode = DeviceModeEnum(required=True)
        rate_watts = graphene.Float()

    device = graphene.Field(DeviceNode)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, device_id, mode, rate_watts=None):
        try:
            device = Device.objects.get(id=device_id)
            mode_str = mode if isinstance(mode, str) else mode.value
            device = DeviceService.set_storage_mode(device, mode_str, rate_watts)
            return SetStorageMode(device=device, success=True, errors=[])
        except Device.DoesNotExist:
            return SetStorageMode(
                device=None,
                success=False,
                errors=[f"Device not found: {device_id}"]
            )
        except DeviceValidationError as e:
            return SetStorageMode(device=None, success=False, errors=[str(e)])
        except Exception as e:
            return SetStorageMode(device=None, success=False, errors=[str(e)])


class Mutation(graphene.ObjectType):
    """Root mutation type."""
    register_device = RegisterDevice.Field()
    set_storage_mode = SetStorageMode.Field()


class Query(graphene.ObjectType):
    """Root query type."""

    devices = graphene.List(
        DeviceNode,
        device_type=DeviceTypeEnum(),
        active_only=graphene.Boolean(default_value=True),
        description="List all devices, optionally filtered by type"
    )

    device = graphene.Field(
        DeviceNode,
        id=graphene.ID(required=True),
        description="Get a single device by ID"
    )

    energy_summary = graphene.Field(
        EnergySummaryType,
        description="Get current energy summary across all devices"
    )

    def resolve_devices(self, info, device_type=None, active_only=True):
        queryset = Device.objects.all()

        if active_only:
            queryset = queryset.filter(is_active=True)

        if device_type:
            queryset = queryset.filter(device_type=device_type)

        return queryset

    def resolve_device(self, info, id):
        try:
            return Device.objects.get(id=id)
        except Device.DoesNotExist:
            return None

    def resolve_energy_summary(self, info):
        summary = EnergyService.get_energy_summary()

        return EnergySummaryType(
            total_production_watts=summary.total_production_watts,
            total_consumption_watts=summary.total_consumption_watts,
            net_power_watts=summary.net_power_watts,
            storage_states=[
                StorageStateType(
                    device_id=s.device_id,
                    device_name=s.device_name,
                    device_type=s.device_type,
                    capacity_wh=s.capacity_wh,
                    current_charge_wh=s.current_charge_wh,
                    charge_percentage=s.charge_percentage,
                    mode=s.mode
                )
                for s in summary.storage_states
            ]
        )


schema = graphene.Schema(query=Query, mutation=Mutation)
