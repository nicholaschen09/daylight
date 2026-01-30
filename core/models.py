import uuid
from django.db import models


# =============================================================================
# SAMPLE DJANGO MODELS - For reference only, not part of the assessment solution. Feel free to delete
#
# related_name usage:
#   category.items.all()       # Get all items in a category (reverse FK)
#   tag.items.all()            # Get all items with a tag (reverse M2M)
#
# CRUD Operations:
#   # Create
#   category = Category.objects.create(name="Electronics")
#   item = Item.objects.create(name="Laptop", category=category)
#   item.tags.add(tag1, tag2)
#
#   # Read
#   Item.objects.all()
#   Item.objects.get(id=1)
#   Item.objects.filter(is_active=True)
#   Item.objects.filter(category__name="Electronics")
#
#   # Update
#   item.name = "New Name"
#   item.save()
#   Item.objects.filter(is_active=False).update(is_active=True)
#
#   # Delete
#   item.delete()
#   Item.objects.filter(is_active=False).delete()
#   item.tags.remove(tag1)
#   item.tags.clear()
# =============================================================================
#


class BaseModel(models.Model):
    """Abstract base model with timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Tag(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Item(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="items",
    )

    tags = models.ManyToManyField(Tag, related_name="items", blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "category"],
                name="unique_item_per_category",
            ),
        ]

    def __str__(self):
        return self.name


class DeviceType(models.TextChoices):
    """Enumeration of supported device types."""
    SOLAR_PANEL = 'solar_panel', 'Solar Panel'
    BATTERY = 'battery', 'Battery'
    ELECTRIC_VEHICLE = 'electric_vehicle', 'Electric Vehicle'
    APPLIANCE = 'appliance', 'Appliance'


class DeviceMode(models.TextChoices):
    """Operating modes for storage devices (Battery, EV)."""
    CHARGING = 'charging', 'Charging'
    DISCHARGING = 'discharging', 'Discharging'
    IDLE = 'idle', 'Idle'


class Device(BaseModel):
    """
    Single table for all device types using STI pattern.

    Common fields stored directly, type-specific properties in JSONField.

    Property schemas by device type:
    - Solar Panel: {"rated_capacity_watts": int}
    - Battery: {"capacity_wh": int, "max_charge_rate_watts": int, "max_discharge_rate_watts": int}
    - Electric Vehicle: {"battery_capacity_wh": int, "max_charge_rate_watts": int, "max_discharge_rate_watts": int}
    - Appliance: {"average_power_draw_watts": int}

    Current state schemas by device type:
    - Solar Panel: {"current_output_watts": float}
    - Battery/EV: {"current_charge_wh": float, "mode": str, "current_rate_watts": float}
    - Appliance: {"is_on": bool, "current_power_draw_watts": float}
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
        db_index=True
    )
    is_active = models.BooleanField(default=True)
    properties = models.JSONField(default=dict)
    current_state = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['device_type', 'is_active']),
            models.Index(fields=['is_active', 'created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()})"

    @property
    def is_producer(self) -> bool:
        """Returns True if device is currently producing energy."""
        if self.device_type == DeviceType.SOLAR_PANEL:
            return self.current_state.get('current_output_watts', 0) > 0
        if self.device_type in [DeviceType.BATTERY, DeviceType.ELECTRIC_VEHICLE]:
            return self.current_state.get('mode') == DeviceMode.DISCHARGING
        return False

    @property
    def is_consumer(self) -> bool:
        """Returns True if device is currently consuming energy."""
        if self.device_type == DeviceType.APPLIANCE:
            return self.current_state.get('is_on', False)
        if self.device_type in [DeviceType.BATTERY, DeviceType.ELECTRIC_VEHICLE]:
            return self.current_state.get('mode') == DeviceMode.CHARGING
        return False

    @property
    def current_power_watts(self) -> float:
        """
        Returns current power in watts.
        Positive = producing, Negative = consuming
        """
        if self.device_type == DeviceType.SOLAR_PANEL:
            return self.current_state.get('current_output_watts', 0)

        if self.device_type == DeviceType.APPLIANCE:
            if self.current_state.get('is_on', False):
                return -self.current_state.get('current_power_draw_watts', 0)
            return 0

        if self.device_type in [DeviceType.BATTERY, DeviceType.ELECTRIC_VEHICLE]:
            mode = self.current_state.get('mode', DeviceMode.IDLE)
            rate = self.current_state.get('current_rate_watts', 0)
            if mode == DeviceMode.DISCHARGING:
                return rate
            elif mode == DeviceMode.CHARGING:
                return -rate
        return 0

    @property
    def charge_percentage(self) -> float | None:
        """Returns charge percentage for storage devices, None for others."""
        if self.device_type not in [DeviceType.BATTERY, DeviceType.ELECTRIC_VEHICLE]:
            return None

        if self.device_type == DeviceType.BATTERY:
            capacity = self.properties.get('capacity_wh', 0)
        else:
            capacity = self.properties.get('battery_capacity_wh', 0)

        current = self.current_state.get('current_charge_wh', 0)

        if capacity > 0:
            return (current / capacity) * 100
        return 0

    @property
    def capacity_wh(self) -> float | None:
        """Returns capacity in Wh for storage devices, None for others."""
        if self.device_type == DeviceType.BATTERY:
            return self.properties.get('capacity_wh')
        elif self.device_type == DeviceType.ELECTRIC_VEHICLE:
            return self.properties.get('battery_capacity_wh')
        return None


class TelemetryReading(BaseModel):
    """
    Time-series telemetry data for devices.

    Optimized for time-range queries with proper indexing.
    """
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='telemetry_readings'
    )
    timestamp = models.DateTimeField(db_index=True)
    power_watts = models.FloatField()
    charge_wh = models.FloatField(null=True, blank=True)
    state_snapshot = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['device', '-timestamp']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['device', 'timestamp'],
                name='unique_device_timestamp'
            )
        ]

    def __str__(self):
        return f"{self.device.name} @ {self.timestamp}: {self.power_watts}W"
