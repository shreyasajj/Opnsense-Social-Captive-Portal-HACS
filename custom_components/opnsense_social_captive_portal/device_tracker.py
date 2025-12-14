"""Device tracker platform for Captive Portal integration."""
from __future__ import annotations

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CaptivePortalCoordinator
from .const import DOMAIN
from .device import person_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Captive Portal device trackers for each person."""
    coordinator: CaptivePortalCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Wait for first data fetch
    await coordinator.async_config_entry_first_refresh()
    
    # Track which people we've already created device trackers for
    if "created_trackers" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["created_trackers"] = set()
    
    created_trackers = hass.data[DOMAIN]["created_trackers"]
    
    def _create_person_trackers():
        """Create device trackers for any new people with phones."""
        if coordinator.data is None:
            return []
        
        people = coordinator.data.get("people", [])
        new_trackers = []
        
        for person in people:
            person_id = person.get("id")
            phone_mac = person.get("phone_mac")
            
            # Only create tracker for people with phones who we haven't seen
            if person_id and phone_mac and person_id not in created_trackers:
                created_trackers.add(person_id)
                new_trackers.append(
                    CaptivePortalDeviceTracker(
                        coordinator,
                        entry,
                        person,
                    )
                )
        
        return new_trackers
    
    # Create initial trackers
    initial_trackers = _create_person_trackers()
    if initial_trackers:
        async_add_entities(initial_trackers)
    
    # Listen for coordinator updates to add new people
    async def _async_update_listener():
        """Handle updated data from the coordinator."""
        new_trackers = _create_person_trackers()
        if new_trackers:
            async_add_entities(new_trackers)
    
    entry.async_on_unload(
        coordinator.async_add_listener(_async_update_listener)
    )


class CaptivePortalDeviceTracker(CoordinatorEntity, TrackerEntity):
    def __init__(self, coordinator, entry, person_data):
        super().__init__(coordinator)
        self._entry = entry
        self._person_id = person_data.get("id")
        self._person_name = person_data.get("name", "Unknown")

        self._attr_name = self._person_name
        self._attr_unique_id = f"{entry.entry_id}_tracker_{self._person_id}"

        # Let HA manage entity_id
        self._attr_source_type = SourceType.ROUTER

        # initialize attrs
        self._attr_is_connected = None
        self._attr_entity_picture = None
        self._attr_extra_state_attributes = {}

    def _find_person(self) -> dict | None:
        if not self.coordinator.data:
            return None
        for p in self.coordinator.data.get("people", []):
            if p.get("id") == self._person_id:
                return p
        return None

    @property
    def is_connected(self) -> bool | None:
        # HA uses this to set home/not_home/unknown
        return self._attr_is_connected

    @property
    def entity_picture(self) -> str | None:
        return self._attr_entity_picture

    @property
    def extra_state_attributes(self) -> dict:
        return self._attr_extra_state_attributes

    @property
    def device_info(self):
        return person_device_info(self._entry, str(self._person_id), self._person_name)

    def _handle_coordinator_update(self) -> None:
        person = self._find_person()

        if person is None:
            self._attr_is_connected = None
            self._attr_entity_picture = None
            self._attr_extra_state_attributes = {
                "person_id": self._person_id,
                "person_name": self._person_name,
                "source": "captive_portal",
            }
        else:
            self._attr_is_connected = bool(person.get("online", False))
            self._attr_entity_picture = person.get("photo")
            self._attr_extra_state_attributes = {
                "person_id": self._person_id,
                "person_name": self._person_name,
                "phone_mac": person.get("phone_mac"),
                "phone_count": person.get("phone_count", 0),
                "source": "captive_portal",
            }

        super()._handle_coordinator_update()
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
                    "phone_mac": person.get("phone_mac"),
                    "phone_count": person.get("phone_count", 0),
                    "source": "captive_portal",
                }
        
        return {"person_id": self._person_id, "person_name": self._person_name}
