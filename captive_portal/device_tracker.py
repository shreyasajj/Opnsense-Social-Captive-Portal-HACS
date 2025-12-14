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
    """Device tracker for a person based on their phone's presence on the network.
    
    - Entity name: {person_name}
    - State: home/not_home based on ARP table polling
    - Attributes: phone_mac, last_seen, photo
    """

    def __init__(
        self,
        coordinator: CaptivePortalCoordinator,
        entry: ConfigEntry,
        person_data: dict,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._person_id = person_data.get("id")
        self._person_name = person_data.get("name", "Unknown")
        self._entry = entry
        
        # Clean name for entity_id
        clean_name = self._person_name.lower().replace(" ", "_")
        clean_name = "".join(c for c in clean_name if c.isalnum() or c == "_")
        
        self._attr_name = self._person_name
        self._attr_unique_id = f"{entry.entry_id}_tracker_{self._person_id}"
        self.entity_id = f"device_tracker.{clean_name}"

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.ROUTER

    @property
    def is_connected(self) -> bool | None:
        """Return true if the device is connected (phone detected on network)."""
        if self.coordinator.data is None:
            return None
        
        people = self.coordinator.data.get("people", [])
        for person in people:
            if person.get("id") == self._person_id:
                return person.get("online", False)
        
        return None

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.is_connected:
            return "mdi:account-check"
        return "mdi:account-off"

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
                    "phone_mac": person.get("phone_mac"),
                    "phone_count": person.get("phone_count", 0),
                    "source": "captive_portal",
                }
        
        return {"person_id": self._person_id, "person_name": self._person_name}
