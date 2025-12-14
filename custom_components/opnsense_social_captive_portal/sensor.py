"""Sensor platform for Captive Portal integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CaptivePortalCoordinator
from .const import DOMAIN
from .device import hub_device_info, person_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Captive Portal sensors based on a config entry."""
    coordinator: CaptivePortalCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Static count sensors
    sensors = [
        CaptivePortalSensor(
            coordinator,
            entry,
            "pending_requests",
            "Pending Requests",
            "pending_count",
            "mdi:account-clock",
        ),
        CaptivePortalSensor(
            coordinator,
            entry,
            "approved_users",
            "Approved Users",
            "approved_count",
            "mdi:account-check",
        ),
        CaptivePortalSensor(
            coordinator,
            entry,
            "tracked_devices",
            "Tracked Devices",
            "tracked_count",
            "mdi:cellphone-marker",
        ),
        CaptivePortalSensor(
            coordinator,
            entry,
            "people",
            "People",
            "people_count",
            "mdi:account-group",
        ),
    ]

    async_add_entities(sensors)
    
    # Track which person_phone sensors we've created
    if "created_phone_sensors" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["created_phone_sensors"] = set()
    
    created_phone_sensors = hass.data[DOMAIN]["created_phone_sensors"]
    
    def _create_person_phone_sensors():
        """Create person_phone sensors for people with phone devices."""
        if coordinator.data is None:
            return []
        
        people = coordinator.data.get("people", [])
        new_sensors = []
        
        for person in people:
            person_id = person.get("id")
            phone_mac = person.get("phone_mac")
            
            # Only create sensor for people with phones who we haven't seen
            if person_id and phone_mac and person_id not in created_phone_sensors:
                created_phone_sensors.add(person_id)
                new_sensors.append(
                    CaptivePortalPersonPhoneSensor(
                        coordinator,
                        entry,
                        person,
                    )
                )
        
        return new_sensors
    
    # Create initial person_phone sensors
    initial_phone_sensors = _create_person_phone_sensors()
    if initial_phone_sensors:
        async_add_entities(initial_phone_sensors)
    
    # Listen for new people with phones
    async def _async_update_listener():
        """Handle updated data from the coordinator."""
        new_sensors = _create_person_phone_sensors()
        if new_sensors:
            async_add_entities(new_sensors)
    
    entry.async_on_unload(
        coordinator.async_add_listener(_async_update_listener)
    )


class CaptivePortalSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Captive Portal count sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: CaptivePortalCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
        name: str,
        data_key: str,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._data_key = data_key
        self._attr_name = f"Captive Portal {name}"
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_icon = icon
        self._attr_device_info = hub_device_info(entry)

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._data_key, 0)


class CaptivePortalPersonPhoneSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing a person's phone MAC address.
    
    Entity name: {person_name}_phone
    Value: MAC address of their primary phone
    Attributes: photo (data URI), online status
    """

    def __init__(
        self,
        coordinator: CaptivePortalCoordinator,
        entry: ConfigEntry,
        person_data: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._person_id = person_data.get("id")
        self._person_name = person_data.get("name", "Unknown")
        
        # Clean name for entity_id
        clean_name = self._person_name.lower().replace(" ", "_")
        clean_name = "".join(c for c in clean_name if c.isalnum() or c == "_")
        
        self._attr_name = f"{self._person_name} Phone"
        self._attr_unique_id = f"{entry.entry_id}_person_phone_{self._person_id}"
        self._attr_icon = "mdi:cellphone"
        self.entity_id = f"sensor.{clean_name}_phone"
        self._attr_device_info = person_device_info(entry, str(self._person_id), self._person_name)

    @property
    def native_value(self) -> str | None:
        """Return the MAC address of the person's phone."""
        if self.coordinator.data is None:
            return None
        
        people = self.coordinator.data.get("people", [])
        for person in people:
            if person.get("id") == self._person_id:
                return person.get("phone_mac")
        
        return None
    
    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture (contact photo) if available."""
        if self.coordinator.data is None:
            return None
        
        people = self.coordinator.data.get("people", [])
        for person in people:
            if person.get("id") == self._person_id:
                return person.get("photo")
        return None
    
    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return {}
        
        people = self.coordinator.data.get("people", [])
        for person in people:
            if person.get("id") == self._person_id:
                return {
                    "person_id": self._person_id,
                    "person_name": self._person_name,
                    "online": person.get("online", False),
                    "phone_count": person.get("phone_count", 0),
                    "has_photo": person.get("photo") is not None,
                }
        
        return {"person_id": self._person_id, "person_name": self._person_name}
