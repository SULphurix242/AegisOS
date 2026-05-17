#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AegisOS Demo - Shows system capabilities without requiring API keys
"""

import asyncio
import sys
from datetime import datetime
from aegisos.config import load_config
from aegisos.store.state import AppState
from aegisos.engine.mock import MockEngine

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def demo():
    print("=" * 70)
    print("AegisOS - AI Agent Immune System Demo")
    print("=" * 70)
    print()
    
    # Load configuration
    print("📋 Loading configuration...")
    config = load_config()
    print(f"   ✓ Providers configured: {', '.join(config.available_providers())}")
    print(f"   ✓ Routing mode: {config.route_mode}")
    print(f"   ✓ Event interval: {config.event_interval}s")
    print()
    
    # Create state
    print("💾 Initializing state store...")
    state = AppState()
    print(f"   ✓ State initialized")
    print()
    
    # Create mock engine
    print("🎭 Creating mock threat engine...")
    
    threat_count = 0
    
    async def on_threat(event):
        nonlocal threat_count
        threat_count += 1
        state.add_event(event)
        
        severity_colors = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🔵",
        }
        
        icon = severity_colors.get(event['severity'], "⚪")
        print(f"   {icon} [{event['severity']:8s}] {event['type']:25s} on {event['agent']}")
    
    async def on_metrics(metrics):
        pass  # Silent for demo
    
    engine = MockEngine(config, on_threat, on_metrics)
    print(f"   ✓ Engine created with {len(engine.get_agents())} agents")
    print()
    
    # Show agents
    print("🤖 Monitored AI Agents:")
    for agent in engine.get_agents():
        print(f"   • {agent['name']:20s} ({agent['role']})")
    print()
    
    # Start engine
    print("🚀 Starting threat detection engine...")
    print("   (Generating simulated threats for 15 seconds...)")
    print()
    
    # Start engine in background
    engine_task = asyncio.create_task(engine.start())
    
    # Run for 15 seconds
    try:
        await asyncio.sleep(15)
    except KeyboardInterrupt:
        print("\n   ⚠️  Interrupted by user")
    
    # Stop engine
    engine.stop()
    engine_task.cancel()
    
    print()
    print("=" * 70)
    print("📊 Demo Summary")
    print("=" * 70)
    print(f"   Total threats detected: {threat_count}")
    print(f"   Events in state: {len(state.events)}")
    print()
    
    # Show threat breakdown
    severity_counts = {}
    type_counts = {}
    
    for event in state.events:
        severity = event.get('severity', 'UNKNOWN')
        threat_type = event.get('type', 'Unknown')
        
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        type_counts[threat_type] = type_counts.get(threat_type, 0) + 1
    
    print("   Threats by Severity:")
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = severity_counts.get(severity, 0)
        if count > 0:
            bar = "█" * (count * 2)
            print(f"      {severity:8s}: {bar} ({count})")
    
    print()
    print("   Top Threat Types:")
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    for threat_type, count in sorted_types[:5]:
        print(f"      • {threat_type:30s}: {count}")
    
    print()
    print("=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("   1. Add your API keys to .env file")
    print("   2. Run: python -m aegisos (Terminal UI)")
    print("   3. Run: python -m aegisos.engine.proxy_server (HTTP Proxy)")
    print()
    print("Documentation:")
    print("   • README.md - Overview")
    print("   • SETUP_GUIDE.md - Setup with your API keys")
    print("   • REAL_TIME_INTEGRATION.md - Integration guide")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
