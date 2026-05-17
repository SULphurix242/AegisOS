#!/usr/bin/env python3
"""
Interactive script to help set up API keys for AegisOS
"""
import os
import sys

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║              AegisOS API Key Setup Helper                 ║
╚═══════════════════════════════════════════════════════════╝

This script will help you configure your API keys.

You mentioned you have API keys for:
  • Groq (llama-3.3-70b-versatile)
  • Cerebras (gpt-oss-120b)
  • Google AI Studio / Gemini (gemini-1.5-flash)

""")
    
    # Check current .env file
    env_path = ".env"
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        print("   Creating from .env.example...")
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as f:
                content = f.read()
            with open(".env", "w") as f:
                f.write(content)
            print("✅ Created .env file")
        else:
            print("❌ .env.example not found either!")
            return 1
    
    # Read current .env
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    # Check for placeholder values
    has_groq = False
    has_cerebras = False
    has_gemini = False
    
    for line in lines:
        if line.startswith("GROQ_API_KEY=") and "your_" not in line.lower():
            has_groq = True
        if line.startswith("CEREBRAS_API_KEY=") and "your_" not in line.lower():
            has_cerebras = True
        if line.startswith("GEMINI_API_KEY=") and "your_" not in line.lower():
            has_gemini = True
    
    print("Current API Key Status:")
    print(f"  {'✅' if has_groq else '❌'} Groq API Key")
    print(f"  {'✅' if has_cerebras else '❌'} Cerebras API Key")
    print(f"  {'✅' if has_gemini else '❌'} Google Gemini API Key")
    print()
    
    if has_groq and has_cerebras and has_gemini:
        print("✅ All API keys are configured!")
        print()
        print("You can now:")
        print("  1. Start the proxy: python start_proxy.py")
        print("  2. Run tests: python test_all_agents.py")
        return 0
    
    print("⚠️  Some API keys are not configured.")
    print()
    print("To configure your API keys:")
    print()
    print("1. Open the .env file in a text editor:")
    print("   notepad .env")
    print()
    print("2. Replace the placeholder values with your actual API keys:")
    print()
    
    if not has_groq:
        print("   GROQ_API_KEY=gsk_your_actual_groq_key_here")
        print("   (Get from: https://console.groq.com/keys)")
        print()
    
    if not has_cerebras:
        print("   CEREBRAS_API_KEY=your_actual_cerebras_key_here")
        print("   (Get from: https://cloud.cerebras.ai/)")
        print()
    
    if not has_gemini:
        print("   GEMINI_API_KEY=AIza_your_actual_gemini_key_here")
        print("   (Get from: https://makersuite.google.com/app/apikey)")
        print()
    
    print("3. Save the file")
    print()
    print("4. Run this script again to verify: python setup_api_keys.py")
    print()
    print("=" * 63)
    print()
    
    # Offer to open .env file
    if sys.platform == "win32":
        response = input("Would you like to open .env in Notepad now? (y/n): ")
        if response.lower() == 'y':
            os.system("notepad .env")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
