"""
Ultra-Simplified FastAPI server for AI-powered legal document analysis
Only 2 endpoints: /health, /analyze-legal-document
No user tracking, no document storage - just pure AI analysis
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

# Import only essential modules
try:
    from gemini_service import GeminiLegalAnalyzer
    from config import settings
    from text_extractor import extract_text_fast
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise

# Initialize Gemini AI analyzer
gemini_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown"""
    global gemini_analyzer
    print("🚀 Starting Legal AI Analysis API...")
    print(f"📊 Python version: {sys.version}")
    print(f"🔧 Port: {os.getenv('PORT', '8000')}")
    print(f"🗝️ Gemini API Key configured: {bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != 'your-gemini-api-key-here')}")
    
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-gemini-api-key-here":
        try:
            gemini_analyzer = GeminiLegalAnalyzer(settings.GEMINI_API_KEY)
            print("✅ Gemini AI analyzer initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini AI: {str(e)}")
            gemini_analyzer = None
    else:
        print("⚠️ Gemini API key not configured")
    
    print("✅ Legal AI Analysis API startup complete")
    yield
    print("🔄 Shutting down Legal AI Analysis API...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Legal AI Analysis API",
    description="Ultra-simplified API for AI-powered legal document analysis with Gemini",
    version="3.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """
    Health check endpoint - confirms API is working
    """
    return {
        "status": "healthy",
        "message": "Legal AI Analysis API is operational",
        "timestamp": datetime.now().isoformat(),
        "ai_enabled": gemini_analyzer is not None,
        "version": "3.0.0"
    }

@app.post("/analyze-legal-document")
async def analyze_legal_document(files: List[UploadFile] = File(...)):
    """
    Analyze legal documents with AI and return results immediately.
    No user tracking, no storage - just pure AI analysis.
    
    Returns format: {"clause": "text", "risk": "High/Medium/Low", "laws": "laws", "summary": "summary"}
    """
    
    # Validate inputs
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    for file in files:
        # Add null check for filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="File has no filename")
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} is not a PDF"
            )
    
    if not gemini_analyzer:
        raise HTTPException(
            status_code=503, 
            detail="AI analysis service unavailable - Gemini API not configured"
        )
    
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"legal_analysis_")
        
        # Process each file
        all_legal_analyses = []
        processed_files = []
        
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            
            # Save uploaded file
            content = await file.read()
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Extract text from PDF
            try:
                extracted_text = extract_text_fast(file_path)
                
                if not extracted_text or len(extracted_text.strip()) < 50:
                    continue  # Skip files with insufficient text
                
                # Analyze with Gemini AI
                clause_analyses = gemini_analyzer.analyze_legal_document(
                    extracted_text, 
                    "Legal Document"
                )
                
                # Convert to requested format
                for analysis in clause_analyses:
                    legal_item = {
                        "clause": analysis.get("clause", ""),
                        "risk": analysis.get("risk", "Medium"),
                        "laws": analysis.get("laws", ""),
                        "summary": analysis.get("summary", "")
                    }
                    all_legal_analyses.append(legal_item)
                
                processed_files.append(file.filename)
                
            except Exception as e:
                print(f"Error processing {file.filename}: {str(e)}")
                continue
        
        # Return immediate results (no storage)
        return {
            "status": "completed",
            "message": f"Successfully analyzed {len(processed_files)} legal documents",
            "files": processed_files,
            "total_documents": len(processed_files),
            "total_clauses_analyzed": len(all_legal_analyses),
            "legal_analysis": all_legal_analyses,
            "analyzed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        
    finally:
        # Cleanup temporary files
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Legal AI Analysis API",
        "version": "3.0.0",
        "status": "operational",
        "ai_enabled": gemini_analyzer is not None,
        "endpoints": [
            "/health - Health check",
            "/analyze-legal-document - AI analysis of legal documents (no user tracking)"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
