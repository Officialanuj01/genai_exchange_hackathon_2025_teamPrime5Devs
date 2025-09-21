#!/usr/bin/env python3
"""
Simple startup script to test and debug the API before deployment
"""

import sys
import os

def check_dependencies():
    """Check if all required modules are available"""
    required_modules = [
        'fastapi',
        'uvicorn',
        'aiofiles',
        'pytesseract',
        'cv2',
        'fitz',  # PyMuPDF
        'google.generativeai',
        'dotenv'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing.append(module)
    
    if missing:
        print(f"\n❌ Missing modules: {', '.join(missing)}")
        return False
    else:
        print("\n✅ All dependencies available")
        return True

def check_environment():
    """Check environment variables"""
    print("\n🔧 Environment Variables:")
    port = os.getenv('PORT', '8000')
    gemini_key = os.getenv('GEMINI_API_KEY', '')
    
    print(f"   PORT: {port}")
    print(f"   GEMINI_API_KEY: {'✅ Set' if gemini_key and gemini_key != 'your-gemini-api-key-here' else '❌ Not set'}")
    
    return bool(gemini_key and gemini_key != 'your-gemini-api-key-here')

def main():
    print("🧪 Pre-deployment check for Legal AI Analysis API\n")
    
    deps_ok = check_dependencies()
    env_ok = check_environment()
    
    if deps_ok and env_ok:
        print("\n✅ All checks passed! Ready for deployment.")
        return 0
    else:
        print("\n❌ Some checks failed. Fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())