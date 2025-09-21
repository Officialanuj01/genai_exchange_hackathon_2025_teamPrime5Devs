#!/usr/bin/env python3
"""
Test script to verify API endpoints work correctly
"""

import asyncio
import tempfile
import os
from fastapi.testclient import TestClient

# Import the app
try:
    from api import app
    print("✅ Successfully imported FastAPI app")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    exit(1)

def test_health_endpoint():
    """Test the health endpoint"""
    with TestClient(app) as client:
        try:
            response = client.get("/health")
            if response.status_code == 200:
                data = response.json()
                print("✅ Health endpoint working!")
                print(f"   Status: {data.get('status')}")
                print(f"   AI Enabled: {data.get('ai_enabled')}")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False

def test_root_endpoint():
    """Test the root endpoint"""
    with TestClient(app) as client:
        try:
            response = client.get("/")
            if response.status_code == 200:
                data = response.json()
                print("✅ Root endpoint working!")
                print(f"   Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            return False

def test_invalid_file_upload():
    """Test file upload validation"""
    with TestClient(app) as client:
        try:
            # Test with non-PDF file
            response = client.post(
                "/analyze-legal-document",
                files={"files": ("test.txt", b"This is not a PDF", "text/plain")}
            )
            if response.status_code == 400:
                print("✅ File validation working!")
                return True
            else:
                print(f"❌ File validation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ File validation error: {e}")
            return False

def main():
    print("🧪 Testing Legal AI Analysis API endpoints\n")
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Root Endpoint", test_root_endpoint),
        ("File Validation", test_invalid_file_upload)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All API tests passed! Ready for deployment.")
        return 0
    else:
        print("❌ Some tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())