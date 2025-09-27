#!/usr/bin/env python3
"""Simple connection test for Hue tool."""

import asyncio
import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from jarvis_hue.hue_client import HueClient
from jarvis_shared.config import JarvisConfig
from jarvis_shared.logger import get_logger


async def test_connection():
    """Test basic connection to Hue Bridge."""
    logger = get_logger("hue.connection.test")

    # Load configuration
    config = JarvisConfig()
    print(config.hue)

    print("🔧 Hue Connection Test")
    print("=" * 30)
    print()

    # Check configuration
    print(f"Bridge IP: {config.hue.bridge_ip or 'Not configured'}")
    print(f"Username: {config.hue.username or 'Not configured'}")
    print(f"Auto-discover: {config.hue.auto_discover}")
    print()

    if not config.hue.username:
        print("❌ No Hue username configured!")
        print(
            "Please set JARVIS_HUE__USERNAME environment variable or update config/default.toml"
        )
        return False

    if not config.hue.bridge_ip and not config.hue.auto_discover:
        print("❌ No Hue bridge IP configured and auto-discovery disabled!")
        print(
            "Please set JARVIS_HUE__BRIDGE_IP environment variable or update config/default.toml"
        )
        return False

    try:
        # Test bridge discovery if needed
        if not config.hue.bridge_ip and config.hue.auto_discover:
            print("🔍 Discovering Hue Bridge...")
            async with HueClient("", config.hue.username) as client:
                bridge_ip = await client.discover_bridge()
                if bridge_ip:
                    print(f"✅ Bridge discovered at: {bridge_ip}")
                    config.hue.bridge_ip = bridge_ip
                else:
                    print("❌ Could not discover Hue Bridge")
                    return False

        # Test connection
        print(f"🔌 Connecting to Hue Bridge at {config.hue.bridge_ip}...")
        async with HueClient(config.hue.bridge_ip, config.hue.username) as client:
            # Try to get lights
            lights = await client.get_lights()
            print(f"✅ Connected successfully! Found {len(lights)} lights")

            # Show first few lights
            if lights:
                print("\n💡 Available lights:")
                for i, light in enumerate(lights[:5]):
                    status = "ON" if light.on else "OFF"
                    print(f"  {i+1}. {light.name} (ID: {light.id}) - {status}")
                if len(lights) > 5:
                    print(f"  ... and {len(lights) - 5} more")

            # Try to get groups
            groups = await client.get_groups()
            print(f"\n🏠 Available groups: {len(groups)}")
            if groups:
                for i, group in enumerate(groups[:3]):
                    print(
                        f"  {i+1}. {group.name} (ID: {group.id}) - {len(group.lights)} lights"
                    )
                if len(groups) > 3:
                    print(f"  ... and {len(groups) - 3} more")

            # Turn on a light
            await client.turn_on_light("6")
            print("✅ Light turned on")
            # Turn off a light
            await client.turn_off_light("6")
            print("✅ Light turned off")

            print("\n🎉 Connection test successful!")
            return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your Hue Bridge is connected to the network")
        print("2. Check that the bridge IP address is correct")
        print(
            "3. Verify that the username is valid (press the bridge button and register if needed)"
        )
        print("4. Ensure your computer is on the same network as the bridge")
        return False


async def main():
    """Main function."""
    success = await test_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
