"""Common test helpers."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


class MockConfigEntry(ConfigEntry):
    """Mock config entry."""

    def __init__(
        self,
        domain: str,
        data: dict,
        version: int = 1,
        entry_id: str = "test",
        title: str = "Mock Title",
    ) -> None:
        """Initialize the mock config entry."""
        super().__init__(
            version=version,
            domain=domain,
            title=title,
            data=data,
            source="test",
            entry_id=entry_id,
            unique_id=None,
            options={},
            minor_version=1,
            discovery_keys=(),
        )

    def add_to_hass(self, hass: HomeAssistant) -> None:
        """Add the mock entry to hass."""
        hass.config_entries._entries[self.entry_id] = self