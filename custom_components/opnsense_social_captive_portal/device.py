"""Device helpers for Captive Portal integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, CONF_HOST, CONF_PORT


def hub_device_info(entry) -> DeviceInfo:
    """Return DeviceInfo for the Captive Portal server (hub)."""
    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT)

    name = f"Captive Portal ({host})" if host else "Captive Portal"

    configuration_url = None
    if host and port:
        configuration_url = f"http://{host}:{port}"

    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=name,
        manufacturer="Captive Portal",
        model="Captive Portal Server",
        configuration_url=configuration_url,
    )


def person_device_info(entry, person_id: str, person_name: str | None = None) -> DeviceInfo:
    """Return DeviceInfo for an individual person/device on the portal."""
    name = person_name or f"Person {person_id}"

    return DeviceInfo(
        identifiers={(DOMAIN, f"person_{person_id}")},
        name=name,
        manufacturer="Captive Portal",
        model="Captive Portal User",
        via_device=(DOMAIN, entry.entry_id),
    )
