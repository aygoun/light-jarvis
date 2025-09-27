#!/usr/bin/env python3
"""Test script to verify Jarvis integration."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jarvis_shared.config import JarvisConfig
from jarvis_main_orchestrator import JarvisAssistant


async def test_basic_functionality():
    """Test basic Jarvis functionality."""
    print("🧪 Testing Jarvis Integration...")
    print("=" * 50)
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = JarvisConfig()
        print("✅ Configuration loaded")
        
        # Initialize assistant
        print("🤖 Initializing Jarvis Assistant...")
        assistant = JarvisAssistant(config)
        await assistant.initialize()
        print("✅ Assistant initialized")
        
        # Test basic chat
        print("💬 Testing basic chat...")
        response = await assistant.process_command("Hello, can you help me?")
        print(f"✅ Chat response: {response[:100]}...")
        
        # Test services status
        print("📊 Checking services status...")
        status = await assistant.get_services_status()
        print(f"✅ Services status: {status}")
        
        # Cleanup
        await assistant.shutdown()
        print("✅ Assistant shutdown complete")
        
        print("=" * 50)
        print("🎉 All tests passed! Jarvis is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def main():
    """Main test function."""
    success = await test_basic_functionality()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
    except Exception as e:
        print(f"❌ Test error: {e}")
        sys.exit(1)
