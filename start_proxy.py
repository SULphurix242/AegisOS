#!/usr/bin/env python3
"""
Quick start script for AegisOS Proxy Server
Restarts the proxy with updated configuration
"""
import subprocess
import sys
import os

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║              Starting AegisOS Proxy Server                ║
╚═══════════════════════════════════════════════════════════╝

This will start the proxy server on http://localhost:8000

Supported Providers:
  ✓ Groq (llama-3.3-70b-versatile)
  ✓ Cerebras (gpt-oss-120b)
  ✓ Google Gemini (gemini-1.5-flash)

Press Ctrl+C to stop the server
""")
    
    try:
        # Run the proxy server
        subprocess.run([sys.executable, "-m", "aegisos.engine.proxy_server"])
    except KeyboardInterrupt:
        print("\n\n✅ Proxy server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
