#!/usr/bin/env python3
"""
Debug script to test each provider individually and show detailed errors
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def test_groq():
    """Test Groq API directly"""
    print("\n" + "="*70)
    print("Testing Groq API Directly")
    print("="*70)
    
    api_key = os.getenv("GROQ_API_KEY")
    print(f"API Key: {api_key[:20]}...")
    
    try:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": "Say hello"}]
            },
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

def test_cerebras():
    """Test Cerebras API directly"""
    print("\n" + "="*70)
    print("Testing Cerebras API Directly")
    print("="*70)
    
    api_key = os.getenv("CEREBRAS_API_KEY")
    print(f"API Key: {api_key[:20]}...")
    
    try:
        response = httpx.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-oss-120b",
                "messages": [{"role": "user", "content": "Say hello"}]
            },
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

def test_gemini():
    """Test Gemini API directly"""
    print("\n" + "="*70)
    print("Testing Gemini API Directly")
    print("="*70)
    
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"API Key: {api_key[:20]}...")
    
    model = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    try:
        response = httpx.post(
            url,
            json={
                "contents": [
                    {
                        "parts": [{"text": "Say hello"}],
                        "role": "user"
                    }
                ]
            },
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("\n🔍 Testing Provider APIs Directly\n")
    
    test_groq()
    test_cerebras()
    test_gemini()
    
    print("\n" + "="*70)
    print("Debug Complete")
    print("="*70 + "\n")
