"""Binary sensor platform for Captive Portal integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
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
    """Set up Captive Portal binary sensors."""
    coordinator: CaptivePortalCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Wait for first data fetch
    await coordinator.async_config_entry_first_refresh()
    
    # Create the approval_pending sensor (always exists)
    sensors = [
        CaptivePortalApprovalPendingSensor(coordinator, entry),
    ]
    
    # Track which people we've already created entities for
    if "created_people" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["created_people"] = set()
    
    created_people = hass.data[DOMAIN]["created_people"]
    
    def _create_person_sensors():
        """Create sensors for any new people."""
        if coordinator.data is None:
            return []
        
        people = coordinator.data.get("people", [])
        new_sensors = []
        
        for person in people:
            person_id = person.get("id")
            if person_id and person_id not in created_people:
                created_people.add(person_id)
                new_sensors.append(
                    CaptivePortalPersonPresenceSensor(
                        coordinator,
                        entry,
                        person,
                    )
                )
        
        return new_sensors
    
    # Add initial person sensors
    initial_person_sensors = _create_person_sensors()
    sensors.extend(initial_person_sensors)
    
    async_add_entities(sensors)
    
    # Listen for coordinator updates to add new people
    async def _async_update_listener():
        """Handle updated data from the coordinator."""
        new_sensors = _create_person_sensors()
        if new_sensors:
            async_add_entities(new_sensors)
    
    entry.async_on_unload(
        coordinator.async_add_listener(_async_update_listener)
    )


class CaptivePortalApprovalPendingSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that is ON when there are pending approval requests.
    
    Use this to trigger a notification to redirect to the admin page.
    """
    
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    
    def __init__(
        self,
        coordinator: CaptivePortalCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = "Captive Portal Approval Pending"
        self._attr_unique_id = f"{entry.entry_id}_approval_pending"
        self._attr_device_info = hub_device_info(entry)
        self._attr_icon = "mdi:account-clock"
        self.entity_id = "binary_sensor.captive_portal_approval_pending"
    
    @property
    def is_on(self) -> bool | None:
        """Return true if there are pending approval requests."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("approval_pending", False)
    
    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return {}
        return {
            "pending_count": self.coordinator.data.get("pending_count", 0),
        }


class CaptivePortalPersonPresenceSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for a person's presence based on their phone being detected."""
    
    _attr_device_class = BinarySensorDeviceClass.PRESENCE
    
    def __init__(
        self,
        coordinator: CaptivePortalCoordinator,
        entry: ConfigEntry,
        person_data: dict,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._person_id = person_data.get("id")
        self._person_name = person_data.get("name", "Unknown")
        self._entry = entry
        
        # Clean name for entity_id
        clean_name = self._person_name.lower().replace(" ", "_")
        clean_name = "".join(c for c in clean_name if c.isalnum() or c == "_")
        
        self._attr_name = f"{self._person_name} Presence"
        self._attr_unique_id = f"{entry.entry_id}_person_{self._person_id}"
        self._attr_icon = "mdi:account"
        self.entity_id = f"binary_sensor.captive_portal_{clean_name}_presence"
    
    @property
    def is_on(self) -> bool | None:
        """Return true if person is home (phone detected)."""
        if self.coordinator.data is None:
            return None
        
        people = self.coordinator.data.get("people", [])
        for person in people:
            if person.get("id") == self._person_id:
                return person.get("online", False)
        
        return None
    
    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture URL if photo is available."""
        if self.coordinator.data is None:
            return None
        
        people = self.coordinator.data.get("people", [])
        for person in people:
            if person.get("id") == self._person_id:
                # Photo is returned as data URI from API
                photo = person.get("photo")
                if photo:
                    return photo
        return None
    
    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes including phone MAC."""
        if self.coordinator.data is None:
            return {}
        
        people = self.coordinator.data.get("people", [])
        for person in people:
            if person.get("id") == self._person_id:
                return {
                    "person_id": self._person_id,
                    "person_name": self._person_name,
                    # This is the key attribute - the phone's MAC address
                    "phone_mac": person.get("phone_mac"),
                    "phone_count": person.get("phone_count", 0),
                    "has_photo": person.get("photo") is not None,
                }
        
        return {"person_id": self._person_id, "person_name": self._person_name}
