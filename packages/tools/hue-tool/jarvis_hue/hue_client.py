"""Philips Hue API client for controlling smart lights."""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import aiohttp
from jarvis_shared.logger import get_logger


@dataclass
class HueLight:
    """Represents a Philips Hue light."""

    id: str
    name: str
    type: str
    model_id: str
    manufacturer_name: str
    product_name: str
    unique_id: str
    on: bool
    brightness: int
    hue: int
    saturation: int
    color_temp: int
    reachable: bool


@dataclass
class HueGroup:
    """Represents a Philips Hue group/room."""

    id: str
    name: str
    type: str
    class_: str
    lights: List[str]
    state: Dict[str, Any]


class HueClient:
    """Client for interacting with Philips Hue Bridge API."""

    def __init__(self, bridge_ip: str, username: str):
        """Initialize Hue client.

        Args:
            bridge_ip: IP address of the Hue Bridge
            username: API username for authentication
        """
        self.bridge_ip = bridge_ip
        self.username = username
        self.base_url = f"http://{bridge_ip}/api/{username}"
        self.logger = get_logger("jarvis.hue.client")
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Hue Bridge API."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        url = f"{self.base_url}/{endpoint}"
        timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout

        try:
            async with self.session.request(
                method, url, json=data, timeout=timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    self.logger.error(f"Hue API error {response.status}: {error_text}")
                    raise Exception(f"Hue API error {response.status}: {error_text}")
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error connecting to Hue Bridge: {e}")
            raise Exception(f"Failed to connect to Hue Bridge: {e}")
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout connecting to Hue Bridge at {self.bridge_ip}")
            raise Exception(f"Timeout connecting to Hue Bridge at {self.bridge_ip}")

    async def discover_bridge(self) -> Optional[str]:
        """Discover Hue Bridge IP address using UPnP."""
        try:
            timeout = aiohttp.ClientTimeout(total=5)  # 5 second timeout for discovery
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get("https://discovery.meethue.com/") as response:
                    if response.status == 200:
                        bridges = await response.json()
                        if bridges:
                            return bridges[0].get("internalipaddress")
        except Exception as e:
            self.logger.warning(f"Bridge discovery failed: {e}")
        return None

    async def register_user(self, device_name: str = "Jarvis") -> Optional[str]:
        """Register a new user with the Hue Bridge.

        Note: The physical button on the bridge must be pressed before calling this.
        """
        try:
            data = {"devicetype": device_name}
            result = await self._make_request("POST", "", data)

            if isinstance(result, list) and len(result) > 0:
                error = result[0].get("error")
                if error:
                    if error.get("type") == 101:  # Link button not pressed
                        raise Exception(
                            "Please press the link button on the Hue Bridge and try again"
                        )
                    else:
                        raise Exception(
                            f"Registration failed: {error.get('description')}"
                        )

                success = result[0].get("success")
                if success:
                    return success.get("username")
        except Exception as e:
            self.logger.error(f"User registration failed: {e}")
            raise
        return None

    async def get_lights(self) -> List[HueLight]:
        """Get all lights from the bridge."""
        try:
            data = await self._make_request("GET", "lights")
            lights = []

            for light_id, light_data in data.items():
                state = light_data.get("state", {})
                light = HueLight(
                    id=light_id,
                    name=light_data.get("name", ""),
                    type=light_data.get("type", ""),
                    model_id=light_data.get("modelid", ""),
                    manufacturer_name=light_data.get("manufacturername", ""),
                    product_name=light_data.get("productname", ""),
                    unique_id=light_data.get("uniqueid", ""),
                    on=state.get("on", False),
                    brightness=state.get("bri", 0),
                    hue=state.get("hue", 0),
                    saturation=state.get("sat", 0),
                    color_temp=state.get("ct", 0),
                    reachable=state.get("reachable", False),
                )
                lights.append(light)

            return lights
        except Exception as e:
            self.logger.error(f"Failed to get lights: {e}")
            raise

    async def get_light_by_name(self, light_name: str) -> Optional[HueLight]:
        """Get a specific light by name."""
        try:
            data = await self._make_request("GET", "lights")
            for light in data.values():
                if light.get("name") == light_name:
                    return HueLight(**light)
        except Exception as e:
            self.logger.error(f"Failed to get light {light_name}: {e}")
            return None

    async def get_light(self, light_id: str) -> Optional[HueLight]:
        """Get a specific light by ID."""
        try:
            data = await self._make_request("GET", f"lights/{light_id}")

            state = data.get("state", {})
            light = HueLight(
                id=light_id,
                name=data.get("name", ""),
                type=data.get("type", ""),
                model_id=data.get("modelid", ""),
                manufacturer_name=data.get("manufacturername", ""),
                product_name=data.get("productname", ""),
                unique_id=data.get("uniqueid", ""),
                on=state.get("on", False),
                brightness=state.get("bri", 0),
                hue=state.get("hue", 0),
                saturation=state.get("sat", 0),
                color_temp=state.get("ct", 0),
                reachable=state.get("reachable", False),
            )
            return light
        except Exception as e:
            self.logger.error(f"Failed to get light {light_id}: {e}")
            return None

    async def set_light_state(self, light_id: str, state: Dict[str, Any]) -> bool:
        """Set the state of a specific light."""
        try:
            await self._make_request("PUT", f"lights/{light_id}/state", state)
            return True
        except Exception as e:
            self.logger.error(f"Failed to set light {light_id} state: {e}")
            return False

    async def turn_on_light(
        self,
        light_id: str,
        brightness: Optional[int] = None,
        color: Optional[Tuple[int, int]] = None,
        color_temp: Optional[int] = None,
    ) -> bool:
        """Turn on a light with optional parameters."""
        state = {"on": True}

        if brightness is not None:
            state["bri"] = max(1, min(254, brightness))

        if color is not None:
            hue, saturation = color
            state["hue"] = max(0, min(65535, hue))
            state["sat"] = max(0, min(254, saturation))

        if color_temp is not None:
            state["ct"] = max(153, min(500, color_temp))

        return await self.set_light_state(light_id, state)

    async def turn_off_light(self, light_id: str) -> bool:
        """Turn off a light."""
        return await self.set_light_state(light_id, {"on": False})

    async def set_brightness(self, light_id: str, brightness: int) -> bool:
        """Set light brightness (1-254)."""
        return await self.set_light_state(
            light_id, {"bri": max(1, min(254, brightness))}
        )

    async def set_color(self, light_id: str, hue: int, saturation: int) -> bool:
        """Set light color using hue and saturation."""
        state = {"hue": max(0, min(65535, hue)), "sat": max(0, min(254, saturation))}
        return await self.set_light_state(light_id, state)

    async def set_color_temp(self, light_id: str, color_temp: int) -> bool:
        """Set light color temperature (153-500)."""
        return await self.set_light_state(
            light_id, {"ct": max(153, min(500, color_temp))}
        )

    async def get_groups(self) -> List[HueGroup]:
        """Get all groups/rooms from the bridge."""
        try:
            data = await self._make_request("GET", "groups")
            groups = []

            for group_id, group_data in data.items():
                group = HueGroup(
                    id=group_id,
                    name=group_data.get("name", ""),
                    type=group_data.get("type", ""),
                    class_=group_data.get("class", ""),
                    lights=group_data.get("lights", []),
                    state=group_data.get("action", {}),
                )
                groups.append(group)

            return groups
        except Exception as e:
            self.logger.error(f"Failed to get groups: {e}")
            raise

    async def set_group_state(self, group_id: str, state: Dict[str, Any]) -> bool:
        """Set the state of a group/room."""
        try:
            await self._make_request("PUT", f"groups/{group_id}/action", state)
            return True
        except Exception as e:
            self.logger.error(f"Failed to set group {group_id} state: {e}")
            return False

    async def turn_on_group(
        self,
        group_id: str,
        brightness: Optional[int] = None,
        color: Optional[Tuple[int, int]] = None,
        color_temp: Optional[int] = None,
    ) -> bool:
        """Turn on all lights in a group."""
        state = {"on": True}

        if brightness is not None:
            state["bri"] = max(1, min(254, brightness))

        if color is not None:
            hue, saturation = color
            state["hue"] = max(0, min(65535, hue))
            state["sat"] = max(0, min(254, saturation))

        if color_temp is not None:
            state["ct"] = max(153, min(500, color_temp))

        return await self.set_group_state(group_id, state)

    async def turn_off_group(self, group_id: str) -> bool:
        """Turn off all lights in a group."""
        return await self.set_group_state(group_id, {"on": False})

    async def set_group_brightness(self, group_id: str, brightness: int) -> bool:
        """Set brightness for all lights in a group."""
        return await self.set_group_state(
            group_id, {"bri": max(1, min(254, brightness))}
        )

    async def set_group_color(self, group_id: str, hue: int, saturation: int) -> bool:
        """Set color for all lights in a group."""
        state = {"hue": max(0, min(65535, hue)), "sat": max(0, min(254, saturation))}
        return await self.set_group_state(group_id, state)

    async def set_group_color_temp(self, group_id: str, color_temp: int) -> bool:
        """Set color temperature for all lights in a group."""
        return await self.set_group_state(
            group_id, {"ct": max(153, min(500, color_temp))}
        )

    def rgb_to_hue_sat(self, r: int, g: int, b: int) -> Tuple[int, int]:
        """Convert RGB values to Hue and Saturation.

        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)

        Returns:
            Tuple of (hue, saturation) for Hue API
        """
        # Normalize RGB values
        r, g, b = r / 255.0, g / 255.0, b / 255.0

        # Find max and min values
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val

        # Calculate saturation
        if max_val == 0:
            sat = 0
        else:
            sat = diff / max_val

        # Calculate hue
        if diff == 0:
            hue = 0
        elif max_val == r:
            hue = ((g - b) / diff) % 6
        elif max_val == g:
            hue = (b - r) / diff + 2
        else:  # max_val == b
            hue = (r - g) / diff + 4

        # Convert to Hue API format
        hue = int(hue * 60 * 182)  # Convert to 0-65535 range
        sat = int(sat * 254)  # Convert to 0-254 range

        return hue, sat
