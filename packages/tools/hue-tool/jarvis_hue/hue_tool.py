"""Hue tool implementation for MCP integration."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from jarvis_shared.logger import get_logger
from jarvis_shared.config import HueConfig
from .hue_client import HueClient


class HueTool:
    """Hue tool for MCP integration."""

    def __init__(self, config: Optional[HueConfig] = None):
        """Initialize Hue tool.

        Args:
            config: Hue configuration (uses defaults if None)
        """
        self.config = config or HueConfig()
        self.bridge_ip = self.config.bridge_ip
        self.username = self.config.username
        self.logger = get_logger("jarvis.hue.tool")
        self.client: Optional[HueClient] = None

    async def _ensure_client(self) -> HueClient:
        """Ensure client is initialized."""
        if not self.client:
            if not self.username:
                raise ValueError(
                    "Hue username is required. Please configure it in the Hue settings."
                )

            if not self.bridge_ip and self.config.auto_discover:
                # Try to discover bridge
                temp_client = HueClient("", self.username)
                try:
                    self.bridge_ip = await temp_client.discover_bridge()
                    if not self.bridge_ip:
                        raise ValueError(
                            "Could not discover Hue Bridge. Please provide bridge_ip in configuration."
                        )
                except Exception as e:
                    self.logger.error(f"Bridge discovery failed: {e}")
                    raise ValueError(
                        "Could not discover Hue Bridge. Please provide bridge_ip in configuration."
                    )
            elif not self.bridge_ip:
                raise ValueError(
                    "Hue bridge_ip is required. Please configure it in the Hue settings."
                )

            self.client = HueClient(self.bridge_ip, self.username)

            # Test connection
            try:
                async with self.client as test_client:
                    await test_client._make_request("GET", "config")
            except Exception as e:
                self.logger.error(
                    f"Failed to connect to Hue Bridge at {self.bridge_ip}: {e}"
                )
                raise ValueError(
                    f"Cannot connect to Hue Bridge at {self.bridge_ip}. Please check the IP address and ensure the bridge is accessible."
                )

        return self.client

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Hue tool operation."""
        try:
            if tool_name == "hue_list_lights":
                return await self._list_lights()
            elif tool_name == "hue_get_light":
                return await self._get_light(arguments)
            elif tool_name == "hue_turn_on_light":
                return await self._turn_on_light(arguments)
            elif tool_name == "hue_turn_off_light":
                return await self._turn_off_light(arguments)
            elif tool_name == "hue_set_brightness":
                return await self._set_brightness(arguments)
            elif tool_name == "hue_set_color":
                return await self._set_color(arguments)
            elif tool_name == "hue_set_color_temp":
                return await self._set_color_temp(arguments)
            elif tool_name == "hue_set_rgb_color":
                return await self._set_rgb_color(arguments)
            elif tool_name == "hue_list_groups":
                return await self._list_groups()
            elif tool_name == "hue_turn_on_group":
                return await self._turn_on_group(arguments)
            elif tool_name == "hue_turn_off_group":
                return await self._turn_off_group(arguments)
            elif tool_name == "hue_set_group_brightness":
                return await self._set_group_brightness(arguments)
            elif tool_name == "hue_set_group_color":
                return await self._set_group_color(arguments)
            elif tool_name == "hue_set_group_color_temp":
                return await self._set_group_color_temp(arguments)
            elif tool_name == "hue_set_group_rgb_color":
                return await self._set_group_rgb_color(arguments)
            else:
                raise ValueError(f"Unknown Hue tool: {tool_name}")

        except Exception as e:
            self.logger.error(f"❌ Hue tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _list_lights(self) -> Dict[str, Any]:
        """List all lights."""
        try:
            client = await self._ensure_client()
            async with client as hue_client:
                lights = await hue_client.get_lights()

                # Convert to serializable format
                light_data = []
                for light in lights:
                    light_data.append(
                        {
                            "id": light.id,
                            "name": light.name,
                            "type": light.type,
                            "model_id": light.model_id,
                            "manufacturer_name": light.manufacturer_name,
                            "product_name": light.product_name,
                            "unique_id": light.unique_id,
                            "on": light.on,
                            "brightness": light.brightness,
                            "hue": light.hue,
                            "saturation": light.saturation,
                            "color_temp": light.color_temp,
                            "reachable": light.reachable,
                        }
                    )

                return {"success": True, "lights": light_data, "total": len(light_data)}
        except Exception as e:
            self.logger.error(f"Failed to list lights: {e}")
            return {"success": False, "error": str(e)}

    async def _get_light_by_name(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific light by name."""
        light_name = arguments.get("light_name")
        if not light_name:
            return {"success": False, "error": "light_name is required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                light = await hue_client.get_light_by_name(light_name)
                if not light:
                    return {"success": False, "error": f"Light {light_name} not found"}

                return {
                    "success": True,
                    "light": {
                        "id": light.id,
                        "name": light.name,
                        "type": light.type,
                        "model_id": light.model_id,
                        "manufacturer_name": light.manufacturer_name,
                        "product_name": light.product_name,
                        "unique_id": light.unique_id,
                        "on": light.on,
                        "brightness": light.brightness,
                        "hue": light.hue,
                        "saturation": light.saturation,
                        "color_temp": light.color_temp,
                        "reachable": light.reachable,
                    },
                }
        except Exception as e:
            self.logger.error(f"Failed to get light {light_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _get_light(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific light by ID."""
        light_id = arguments.get("light_id")
        if not light_id:
            return {"success": False, "error": "light_id is required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                light = await hue_client.get_light(light_id)
                if not light:
                    return {"success": False, "error": f"Light {light_id} not found"}

                return {
                    "success": True,
                    "light": {
                        "id": light.id,
                        "name": light.name,
                        "type": light.type,
                        "model_id": light.model_id,
                        "manufacturer_name": light.manufacturer_name,
                        "product_name": light.product_name,
                        "unique_id": light.unique_id,
                        "on": light.on,
                        "brightness": light.brightness,
                        "hue": light.hue,
                        "saturation": light.saturation,
                        "color_temp": light.color_temp,
                        "reachable": light.reachable,
                    },
                }
        except Exception as e:
            self.logger.error(f"Failed to get light {light_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _turn_on_light(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Turn on a light with optional parameters."""
        light_id = arguments.get("light_id")
        if not light_id:
            return {"success": False, "error": "light_id is required"}

        brightness = arguments.get("brightness")
        hue = arguments.get("hue")
        saturation = arguments.get("saturation")
        color_temp = arguments.get("color_temp")
        r = arguments.get("r")
        g = arguments.get("g")
        b = arguments.get("b")

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                # Handle RGB color
                if r is not None and g is not None and b is not None:
                    hue, saturation = hue_client.rgb_to_hue_sat(r, g, b)

                success = await hue_client.turn_on_light(
                    light_id,
                    brightness=brightness,
                    color=(
                        (hue, saturation)
                        if hue is not None and saturation is not None
                        else None
                    ),
                    color_temp=color_temp,
                )

                if success:
                    return {"success": True, "message": f"Light {light_id} turned on"}
                else:
                    return {
                        "success": False,
                        "error": f"Failed to turn on light {light_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to turn on light {light_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _turn_off_light(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Turn off a light."""
        light_id = arguments.get("light_id")
        if not light_id:
            return {"success": False, "error": "light_id is required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                success = await hue_client.turn_off_light(light_id)

                if success:
                    return {"success": True, "message": f"Light {light_id} turned off"}
                else:
                    return {
                        "success": False,
                        "error": f"Failed to turn off light {light_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to turn off light {light_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _set_brightness(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Set light brightness."""
        light_id = arguments.get("light_id")
        brightness = arguments.get("brightness")

        if not light_id:
            return {"success": False, "error": "light_id is required"}
        if brightness is None:
            return {"success": False, "error": "brightness is required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                success = await hue_client.set_brightness(light_id, brightness)

                if success:
                    return {
                        "success": True,
                        "message": f"Light {light_id} brightness set to {brightness}",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to set brightness for light {light_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to set brightness for light {light_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _set_color(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Set light color using hue and saturation."""
        light_id = arguments.get("light_id")
        hue = arguments.get("hue")
        saturation = arguments.get("saturation")

        if not light_id:
            return {"success": False, "error": "light_id is required"}
        if hue is None or saturation is None:
            return {"success": False, "error": "hue and saturation are required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                success = await hue_client.set_color(light_id, hue, saturation)

                if success:
                    return {
                        "success": True,
                        "message": f"Light {light_id} color set to hue={hue}, sat={saturation}",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to set color for light {light_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to set color for light {light_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _set_color_temp(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Set light color temperature."""
        light_id = arguments.get("light_id")
        color_temp = arguments.get("color_temp")

        if not light_id:
            return {"success": False, "error": "light_id is required"}
        if color_temp is None:
            return {"success": False, "error": "color_temp is required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                success = await hue_client.set_color_temp(light_id, color_temp)

                if success:
                    return {
                        "success": True,
                        "message": f"Light {light_id} color temperature set to {color_temp}",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to set color temperature for light {light_id}",
                    }
        except Exception as e:
            self.logger.error(
                f"Failed to set color temperature for light {light_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    async def _set_rgb_color(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Set light color using RGB values."""
        light_id = arguments.get("light_id")
        r = arguments.get("r")
        g = arguments.get("g")
        b = arguments.get("b")

        if not light_id:
            return {"success": False, "error": "light_id is required"}
        if r is None or g is None or b is None:
            return {"success": False, "error": "r, g, and b are required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                hue, saturation = hue_client.rgb_to_hue_sat(r, g, b)
                success = await hue_client.set_color(light_id, hue, saturation)

                if success:
                    return {
                        "success": True,
                        "message": f"Light {light_id} color set to RGB({r}, {g}, {b})",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to set RGB color for light {light_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to set RGB color for light {light_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _list_groups(self) -> Dict[str, Any]:
        """List all groups/rooms."""
        try:
            client = await self._ensure_client()
            async with client as hue_client:
                groups = await hue_client.get_groups()

                # Convert to serializable format
                group_data = []
                for group in groups:
                    group_data.append(
                        {
                            "id": group.id,
                            "name": group.name,
                            "type": group.type,
                            "class": group.class_,
                            "lights": group.lights,
                            "state": group.state,
                        }
                    )

                return {"success": True, "groups": group_data, "total": len(group_data)}
        except Exception as e:
            self.logger.error(f"Failed to list groups: {e}")
            return {"success": False, "error": str(e)}

    async def _turn_on_group(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Turn on all lights in a group."""
        group_id = arguments.get("group_id")
        if not group_id:
            return {"success": False, "error": "group_id is required"}

        brightness = arguments.get("brightness")
        hue = arguments.get("hue")
        saturation = arguments.get("saturation")
        color_temp = arguments.get("color_temp")
        r = arguments.get("r")
        g = arguments.get("g")
        b = arguments.get("b")

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                # Handle RGB color
                if r is not None and g is not None and b is not None:
                    hue, saturation = hue_client.rgb_to_hue_sat(r, g, b)

                success = await hue_client.turn_on_group(
                    group_id,
                    brightness=brightness,
                    color=(
                        (hue, saturation)
                        if hue is not None and saturation is not None
                        else None
                    ),
                    color_temp=color_temp,
                )

                if success:
                    return {"success": True, "message": f"Group {group_id} turned on"}
                else:
                    return {
                        "success": False,
                        "error": f"Failed to turn on group {group_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to turn on group {group_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _turn_off_group(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Turn off all lights in a group."""
        group_id = arguments.get("group_id")
        if not group_id:
            return {"success": False, "error": "group_id is required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                success = await hue_client.turn_off_group(group_id)

                if success:
                    return {"success": True, "message": f"Group {group_id} turned off"}
                else:
                    return {
                        "success": False,
                        "error": f"Failed to turn off group {group_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to turn off group {group_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _set_group_brightness(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Set brightness for all lights in a group."""
        group_id = arguments.get("group_id")
        brightness = arguments.get("brightness")

        if not group_id:
            return {"success": False, "error": "group_id is required"}
        if brightness is None:
            return {"success": False, "error": "brightness is required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                success = await hue_client.set_group_brightness(group_id, brightness)

                if success:
                    return {
                        "success": True,
                        "message": f"Group {group_id} brightness set to {brightness}",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to set brightness for group {group_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to set brightness for group {group_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _set_group_color(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Set color for all lights in a group."""
        group_id = arguments.get("group_id")
        hue = arguments.get("hue")
        saturation = arguments.get("saturation")

        if not group_id:
            return {"success": False, "error": "group_id is required"}
        if hue is None or saturation is None:
            return {"success": False, "error": "hue and saturation are required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                success = await hue_client.set_group_color(group_id, hue, saturation)

                if success:
                    return {
                        "success": True,
                        "message": f"Group {group_id} color set to hue={hue}, sat={saturation}",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to set color for group {group_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to set color for group {group_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _set_group_color_temp(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Set color temperature for all lights in a group."""
        group_id = arguments.get("group_id")
        color_temp = arguments.get("color_temp")

        if not group_id:
            return {"success": False, "error": "group_id is required"}
        if color_temp is None:
            return {"success": False, "error": "color_temp is required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                success = await hue_client.set_group_color_temp(group_id, color_temp)

                if success:
                    return {
                        "success": True,
                        "message": f"Group {group_id} color temperature set to {color_temp}",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to set color temperature for group {group_id}",
                    }
        except Exception as e:
            self.logger.error(
                f"Failed to set color temperature for group {group_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    async def _set_group_rgb_color(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Set color for all lights in a group using RGB values."""
        group_id = arguments.get("group_id")
        r = arguments.get("r")
        g = arguments.get("g")
        b = arguments.get("b")

        if not group_id:
            return {"success": False, "error": "group_id is required"}
        if r is None or g is None or b is None:
            return {"success": False, "error": "r, g, and b are required"}

        try:
            client = await self._ensure_client()
            async with client as hue_client:
                hue, saturation = hue_client.rgb_to_hue_sat(r, g, b)
                success = await hue_client.set_group_color(group_id, hue, saturation)

                if success:
                    return {
                        "success": True,
                        "message": f"Group {group_id} color set to RGB({r}, {g}, {b})",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to set RGB color for group {group_id}",
                    }
        except Exception as e:
            self.logger.error(f"Failed to set RGB color for group {group_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP registration from tools.json."""
        try:
            # Find the tools.json file relative to this file
            current_file = Path(__file__).resolve()
            # Go up: gmail_tool.py -> jarvis_gmail -> gmail-tool -> tools -> packages -> jarvis -> config
            tools_json_path = (
                current_file.parent.parent.parent.parent.parent
                / "config"
                / "tools.json"
            )

            if tools_json_path.exists():
                with open(tools_json_path, "r") as f:
                    tools_config = json.load(f)
                    return tools_config.get("hue", [])
            else:
                self.logger.warning(f"Tools config file not found at {tools_json_path}")
                return []
        except Exception as e:
            self.logger.error(f"Failed to load Hue tool definitions: {e}")
            return []
