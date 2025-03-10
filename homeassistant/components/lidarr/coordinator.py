"""Data update coordinator for the Lidarr integration."""
from __future__ import annotations

from abc import abstractmethod
from datetime import timedelta
from typing import Generic, TypeVar, cast

from aiopyarr import LidarrAlbum, LidarrQueue, LidarrRootFolder, exceptions
from aiopyarr.lidarr_client import LidarrClient
from aiopyarr.models.host_configuration import PyArrHostConfiguration

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_MAX_RECORDS, DOMAIN, LOGGER

T = TypeVar("T", list[LidarrRootFolder], LidarrQueue, str, LidarrAlbum)


class LidarrDataUpdateCoordinator(DataUpdateCoordinator, Generic[T]):
    """Data update coordinator for the Lidarr integration."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        host_configuration: PyArrHostConfiguration,
        api_client: LidarrClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.api_client = api_client
        self.host_configuration = host_configuration
        self.system_version: str | None = None

    async def _async_update_data(self) -> T:
        """Get the latest data from Lidarr."""
        try:
            return await self._fetch_data()

        except exceptions.ArrConnectionException as ex:
            raise UpdateFailed(ex) from ex
        except exceptions.ArrAuthenticationException as ex:
            raise ConfigEntryAuthFailed(
                "API Key is no longer valid. Please reauthenticate"
            ) from ex

    @abstractmethod
    async def _fetch_data(self) -> T:
        """Fetch the actual data."""
        raise NotImplementedError


class DiskSpaceDataUpdateCoordinator(LidarrDataUpdateCoordinator):
    """Disk space update coordinator for Lidarr."""

    async def _fetch_data(self) -> list[LidarrRootFolder]:
        """Fetch the data."""
        return cast(list, await self.api_client.async_get_root_folders())


class QueueDataUpdateCoordinator(LidarrDataUpdateCoordinator):
    """Queue update coordinator."""

    async def _fetch_data(self) -> LidarrQueue:
        """Fetch the album count in queue."""
        return await self.api_client.async_get_queue(page_size=DEFAULT_MAX_RECORDS)


class StatusDataUpdateCoordinator(LidarrDataUpdateCoordinator):
    """Status update coordinator for Lidarr."""

    async def _fetch_data(self) -> str:
        """Fetch the data."""
        return (await self.api_client.async_get_system_status()).version


class WantedDataUpdateCoordinator(LidarrDataUpdateCoordinator):
    """Wanted update coordinator."""

    async def _fetch_data(self) -> LidarrAlbum:
        """Fetch the wanted data."""
        return cast(
            LidarrAlbum,
            await self.api_client.async_get_wanted(page_size=DEFAULT_MAX_RECORDS),
        )
