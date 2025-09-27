#!/usr/bin/env python3
"""Test script for Hue tool to verify connection and functionality."""

import asyncio
import json
import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from jarvis_hue.hue_tool import HueTool
from jarvis_hue.hue_client import HueClient
from jarvis_shared.config import HueConfig
from jarvis_shared.logger import get_logger


class HueToolTester:
    """Test class for Hue tool functionality."""

    def __init__(self):
        self.logger = get_logger("hue.tester")
        self.hue_tool = None
        self.test_results = []

    async def setup(self):
        """Setup the test environment."""
        self.logger.info("🔧 Setting up Hue tool test environment...")

        # Load configuration
        config = HueConfig()

        # Check if we have the required configuration
        if not config.username:
            self.logger.warning(
                "⚠️ No Hue username configured. Some tests will be skipped."
            )
            self.logger.info(
                "To configure Hue username, update config/default.toml or set JARVIS_HUE__USERNAME environment variable"
            )

        if not config.bridge_ip and not config.auto_discover:
            self.logger.warning(
                "⚠️ No Hue bridge IP configured and auto-discovery disabled. Some tests will be skipped."
            )
            self.logger.info(
                "To configure Hue bridge IP, update config/default.toml or set JARVIS_HUE__BRIDGE_IP environment variable"
            )

        self.hue_tool = HueTool(config)
        self.logger.info("✅ Hue tool initialized")

    async def test_bridge_discovery(self):
        """Test bridge discovery functionality."""
        self.logger.info("🔍 Testing bridge discovery...")

        try:
            async with HueClient("", "test") as client:
                bridge_ip = await client.discover_bridge()
                if bridge_ip:
                    self.logger.info(f"✅ Bridge discovered at: {bridge_ip}")
                    self.test_results.append(
                        ("Bridge Discovery", True, f"Found bridge at {bridge_ip}")
                    )
                else:
                    self.logger.warning("⚠️ No bridge discovered")
                    self.test_results.append(
                        ("Bridge Discovery", False, "No bridge found")
                    )
        except Exception as e:
            self.logger.error(f"❌ Bridge discovery failed: {e}")
            self.test_results.append(("Bridge Discovery", False, str(e)))

    async def test_connection(self):
        """Test connection to Hue Bridge."""
        self.logger.info("🔌 Testing connection to Hue Bridge...")

        try:
            # Test basic connection
            client = await self.hue_tool._ensure_client()
            async with client as hue_client:
                # Try to get lights to test connection
                lights = await hue_client.get_lights()
                self.logger.info(
                    f"✅ Connected to Hue Bridge. Found {len(lights)} lights"
                )
                self.test_results.append(
                    ("Connection", True, f"Connected, found {len(lights)} lights")
                )

                # Log first few lights for debugging
                for i, light in enumerate(lights[:3]):
                    self.logger.info(
                        f"  Light {i+1}: {light.name} (ID: {light.id}, On: {light.on})"
                    )

        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            self.test_results.append(("Connection", False, str(e)))

    async def test_list_lights(self):
        """Test listing lights functionality."""
        self.logger.info("💡 Testing list lights...")

        try:
            result = await self.hue_tool.execute("hue_list_lights", {})

            if result.get("success"):
                lights = result.get("lights", [])
                self.logger.info(f"✅ Listed {len(lights)} lights successfully")
                self.test_results.append(
                    ("List Lights", True, f"Listed {len(lights)} lights")
                )

                # Show details of first few lights
                for i, light in enumerate(lights[:3]):
                    self.logger.info(
                        f"  {light['name']}: {light['type']} (ID: {light['id']})"
                    )
            else:
                self.logger.error(f"❌ List lights failed: {result.get('error')}")
                self.test_results.append(
                    ("List Lights", False, result.get("error", "Unknown error"))
                )

        except Exception as e:
            self.logger.error(f"❌ List lights test failed: {e}")
            self.test_results.append(("List Lights", False, str(e)))

    async def test_list_groups(self):
        """Test listing groups functionality."""
        self.logger.info("🏠 Testing list groups...")

        try:
            result = await self.hue_tool.execute("hue_list_groups", {})

            if result.get("success"):
                groups = result.get("groups", [])
                self.logger.info(f"✅ Listed {len(groups)} groups successfully")
                self.test_results.append(
                    ("List Groups", True, f"Listed {len(groups)} groups")
                )

                # Show details of groups
                for group in groups:
                    self.logger.info(
                        f"  {group['name']}: {group['class']} (ID: {group['id']}, Lights: {len(group['lights'])})"
                    )
            else:
                self.logger.error(f"❌ List groups failed: {result.get('error')}")
                self.test_results.append(
                    ("List Groups", False, result.get("error", "Unknown error"))
                )

        except Exception as e:
            self.logger.error(f"❌ List groups test failed: {e}")
            self.test_results.append(("List Groups", False, str(e)))

    async def test_light_control(self, light_id: str):
        """Test light control functionality."""
        self.logger.info(f"🎛️ Testing light control for light {light_id}...")

        try:
            # Test getting light details
            result = await self.hue_tool.execute(
                "hue_get_light", {"light_id": light_id}
            )
            if result.get("success"):
                light = result.get("light")
                self.logger.info(f"✅ Retrieved light details: {light['name']}")
                self.test_results.append(
                    ("Get Light", True, f"Retrieved {light['name']}")
                )
            else:
                self.logger.warning(
                    f"⚠️ Could not get light details: {result.get('error')}"
                )
                self.test_results.append(
                    ("Get Light", False, result.get("error", "Unknown error"))
                )
                return

            # Test turning on light
            result = await self.hue_tool.execute(
                "hue_turn_on_light", {"light_id": light_id, "brightness": 128}
            )
            if result.get("success"):
                self.logger.info("✅ Turned on light successfully")
                self.test_results.append(("Turn On Light", True, "Light turned on"))
            else:
                self.logger.warning(f"⚠️ Could not turn on light: {result.get('error')}")
                self.test_results.append(
                    ("Turn On Light", False, result.get("error", "Unknown error"))
                )

            # Wait a moment
            await asyncio.sleep(1)

            # Test setting brightness
            result = await self.hue_tool.execute(
                "hue_set_brightness", {"light_id": light_id, "brightness": 200}
            )
            if result.get("success"):
                self.logger.info("✅ Set brightness successfully")
                self.test_results.append(("Set Brightness", True, "Brightness set"))
            else:
                self.logger.warning(
                    f"⚠️ Could not set brightness: {result.get('error')}"
                )
                self.test_results.append(
                    ("Set Brightness", False, result.get("error", "Unknown error"))
                )

            # Wait a moment
            await asyncio.sleep(1)

            # Test setting color (red)
            result = await self.hue_tool.execute(
                "hue_set_rgb_color", {"light_id": light_id, "r": 255, "g": 0, "b": 0}
            )
            if result.get("success"):
                self.logger.info("✅ Set color successfully")
                self.test_results.append(("Set Color", True, "Color set to red"))
            else:
                self.logger.warning(f"⚠️ Could not set color: {result.get('error')}")
                self.test_results.append(
                    ("Set Color", False, result.get("error", "Unknown error"))
                )

            # Wait a moment
            await asyncio.sleep(2)

            # Test turning off light
            result = await self.hue_tool.execute(
                "hue_turn_off_light", {"light_id": light_id}
            )
            if result.get("success"):
                self.logger.info("✅ Turned off light successfully")
                self.test_results.append(("Turn Off Light", True, "Light turned off"))
            else:
                self.logger.warning(
                    f"⚠️ Could not turn off light: {result.get('error')}"
                )
                self.test_results.append(
                    ("Turn Off Light", False, result.get("error", "Unknown error"))
                )

        except Exception as e:
            self.logger.error(f"❌ Light control test failed: {e}")
            self.test_results.append(("Light Control", False, str(e)))

    async def test_group_control(self, group_id: str):
        """Test group control functionality."""
        self.logger.info(f"🏠 Testing group control for group {group_id}...")

        try:
            # Test turning on group
            result = await self.hue_tool.execute(
                "hue_turn_on_group", {"group_id": group_id, "brightness": 100}
            )
            if result.get("success"):
                self.logger.info("✅ Turned on group successfully")
                self.test_results.append(("Turn On Group", True, "Group turned on"))
            else:
                self.logger.warning(f"⚠️ Could not turn on group: {result.get('error')}")
                self.test_results.append(
                    ("Turn On Group", False, result.get("error", "Unknown error"))
                )

            # Wait a moment
            await asyncio.sleep(1)

            # Test setting group color (blue)
            result = await self.hue_tool.execute(
                "hue_set_group_rgb_color",
                {"group_id": group_id, "r": 0, "g": 0, "b": 255},
            )
            if result.get("success"):
                self.logger.info("✅ Set group color successfully")
                self.test_results.append(
                    ("Set Group Color", True, "Group color set to blue")
                )
            else:
                self.logger.warning(
                    f"⚠️ Could not set group color: {result.get('error')}"
                )
                self.test_results.append(
                    ("Set Group Color", False, result.get("error", "Unknown error"))
                )

            # Wait a moment
            await asyncio.sleep(2)

            # Test turning off group
            result = await self.hue_tool.execute(
                "hue_turn_off_group", {"group_id": group_id}
            )
            if result.get("success"):
                self.logger.info("✅ Turned off group successfully")
                self.test_results.append(("Turn Off Group", True, "Group turned off"))
            else:
                self.logger.warning(
                    f"⚠️ Could not turn off group: {result.get('error')}"
                )
                self.test_results.append(
                    ("Turn Off Group", False, result.get("error", "Unknown error"))
                )

        except Exception as e:
            self.logger.error(f"❌ Group control test failed: {e}")
            self.test_results.append(("Group Control", False, str(e)))

    async def run_all_tests(self):
        """Run all tests."""
        self.logger.info("🚀 Starting Hue tool tests...")

        await self.setup()

        # Test bridge discovery
        await self.test_bridge_discovery()

        # Test connection
        await self.test_connection()

        # Test listing functionality
        await self.test_list_lights()
        await self.test_list_groups()

        # Get first light and group for control tests
        try:
            lights_result = await self.hue_tool.execute("hue_list_lights", {})
            groups_result = await self.hue_tool.execute("hue_list_groups", {})

            if lights_result.get("success") and lights_result.get("lights"):
                first_light = lights_result["lights"][0]
                await self.test_light_control(first_light["id"])

            if groups_result.get("success") and groups_result.get("groups"):
                first_group = groups_result["groups"][0]
                await self.test_group_control(first_group["id"])

        except Exception as e:
            self.logger.error(f"❌ Control tests failed: {e}")

        # Print results
        self.print_results()

    def print_results(self):
        """Print test results summary."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 TEST RESULTS SUMMARY")
        self.logger.info("=" * 60)

        passed = 0
        failed = 0

        for test_name, success, message in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            self.logger.info(f"{status} {test_name}: {message}")
            if success:
                passed += 1
            else:
                failed += 1

        self.logger.info("=" * 60)
        self.logger.info(f"Total: {passed + failed} tests")
        self.logger.info(f"Passed: {passed}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info("=" * 60)

        if failed == 0:
            self.logger.info("🎉 All tests passed!")
        else:
            self.logger.warning(
                f"⚠️ {failed} test(s) failed. Check configuration and connection."
            )


async def main():
    """Main test function."""
    print("🔧 Hue Tool Test Suite")
    print("=" * 40)
    print()
    print("This test will verify the Hue tool connection and functionality.")
    print("Make sure your Hue Bridge is connected and configured properly.")
    print()

    # Check if user wants to continue
    try:
        response = input("Continue with tests? (y/N): ").strip().lower()
        if response not in ["y", "yes"]:
            print("Test cancelled.")
            return
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        return

    print()

    tester = HueToolTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
