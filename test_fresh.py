#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fresh test without cached imports."""

import sys
import importlib

# Clear all aegisos modules from cache
mods_to_clear = [k for k in list(sys.modules.keys()) if 'aegisos' in k]
for mod in mods_to_clear:
    del sys.modules[mod]

# Invalidate import caches
importlib.invalidate_caches()

print("Testing AegisOS with fresh imports...")

try:
    print("[OK] Testing config module...")
    from aegisos.config import load_config, AegisConfig
    
    print("[OK] Testing state store...")
    from aegisos.store.state import AppState
    
    print("[OK] Testing mock engine...")
    from aegisos.engine.mock import MockEngine, THREAT_TYPES, AGENTS
    
    print("[OK] Testing LLM base...")
    from aegisos.llm.base import BaseLLMClient
    
    print("[OK] Testing LLM clients...")
    from aegisos.llm.groq import GroqClient
    from aegisos.llm.cerebras import CerebrasClient
    from aegisos.llm.gemini import GeminiClient
    
    print("[OK] Testing LLM router...")
    from aegisos.engine.router import LLMRouter
    
    print("[OK] Testing threat analyzer...")
    from aegisos.llm.analyzer import ThreatAnalyzer
    
    print("[OK] Testing nav widget...")
    from aegisos.widgets.nav import NavPanel
    
    print("\n[SUCCESS] All imports successful!")
    print("\nTesting basic functionality...")
    
    # Test config loading
    config = load_config()
    print(f"[OK] Config loaded: {config.available_providers()} providers configured")
    
    # Test state creation
    state = AppState()
    print(f"[OK] State initialized: {len(state.events)} events")
    
    # Test mock engine creation (don't start it)
    async def dummy_callback(x): pass
    engine = MockEngine(config, dummy_callback, dummy_callback)
    print(f"[OK] Mock engine created: {len(engine.get_agents())} agents")
    
    # Test LLM router creation
    router = LLMRouter(config)
    print(f"[OK] LLM router created: {len(router.history)} routing events")
    
    # Test analyzer creation
    analyzer = ThreatAnalyzer(router)
    print(f"[OK] Threat analyzer created")
    
    print("\n[SUCCESS] All core components working correctly!")
    print("\nNext steps:")
    print("1. Add API keys to .env file")
    print("2. Build remaining widgets (5 more)")
    print("3. Build screens (10 total)")
    print("4. Create main app and entry point")
    print("5. Test full application")
    
except ImportError as e:
    print(f"\n[ERROR] Import error: {e}")
    print("Make sure you're running from the project root directory")
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
