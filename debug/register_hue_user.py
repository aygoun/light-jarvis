#!/usr/bin/env python3
"""Script to register a new Hue username with the bridge."""

import asyncio
import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from jarvis_hue.hue_client import HueClient
from jarvis_shared.config import HueConfig
from jarvis_shared.logger import get_logger


async def register_user():
    """Register a new user with the Hue Bridge."""
    logger = get_logger("hue.user.registration")

    # Load configuration
    config = HueConfig()

    print("🔐 Hue Bridge User Registration")
    print("=" * 40)
    print()
    print("This script will help you register a new username with your Hue Bridge.")
    print(
        "You'll need to press the physical button on your Hue Bridge during registration."
    )
    print()

    # Get bridge IP
    bridge_ip = config.bridge_ip
    if not bridge_ip:
        print("🔍 Discovering Hue Bridge...")
        async with HueClient("", "") as client:
            bridge_ip = await client.discover_bridge()
            if not bridge_ip:
                print("❌ Could not discover Hue Bridge automatically.")
                bridge_ip = input("Please enter your Hue Bridge IP address: ").strip()
                if not bridge_ip:
                    print("❌ No bridge IP provided. Exiting.")
                    return False
            else:
                print(f"✅ Found bridge at: {bridge_ip}")

    # Get device name
    device_name = input("Enter a name for this device (default: 'Jarvis'): ").strip()
    if not device_name:
        device_name = "Jarvis"

    print()
    print("⚠️  IMPORTANT: Press the physical button on your Hue Bridge NOW!")
    print("   You have 30 seconds to press the button...")
    print()

    try:
        # Countdown
        for i in range(30, 0, -1):
            print(f"\r⏰ {i} seconds remaining...", end="", flush=True)
            await asyncio.sleep(1)
        print()

        # Attempt registration
        print("🔄 Attempting to register user...")
        async with HueClient(bridge_ip, "") as client:
            username = await client.register_user(device_name)

            if username:
                print("✅ Registration successful!")
                print(f"Username: {username}")
                print()
                print("📝 Add this to your configuration:")
                print(f"   JARVIS_HUE__USERNAME={username}")
                print("   or update config/default.toml:")
                print("   [hue]")
                print(f'   username = "{username}"')
                print()
                print("🎉 You can now use the Hue tool!")
                return True
            else:
                print("❌ Registration failed. Please try again.")
                return False

    except Exception as e:
        print(f"❌ Registration failed: {e}")
        print()
        print("Common issues:")
        print("1. Button not pressed within 30 seconds")
        print("2. Bridge not accessible on the network")
        print("3. Bridge already has maximum users (10)")
        print("4. Network connectivity issues")
        return False


async def main():
    """Main function."""
    success = await register_user()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
