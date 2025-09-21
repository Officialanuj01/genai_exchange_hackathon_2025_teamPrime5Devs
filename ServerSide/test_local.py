#!/usr/bin/env python3
"""
Simple test script to verify the API works locally before deploying
"""

import requests
import json
import sys

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint working!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health endpoint failed with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

def main():
    print("🧪 Testing Legal AI Analysis API locally...")
    
    if test_health_endpoint():
        print("✅ Local API test passed!")
        sys.exit(0)
    else:
        print("❌ Local API test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()