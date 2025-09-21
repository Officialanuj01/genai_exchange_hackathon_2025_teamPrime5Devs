"""
Ultra-Simplified FastAPI server for AI-powered legal document analysis
Only 2 endpoints: /health, /analyze-legal-document
No user tracking, no document storage - just pure AI analysis
"""

import os
import sys
import tempfile
import shutil
import asyncio
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
    from job_manager import job_manager, JobStatus
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
    try:
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
            gemini_analyzer = None
        
        print("✅ Legal AI Analysis API startup complete")
        yield
        print("🔄 Shutting down Legal AI Analysis API...")
    except Exception as e:
        print(f"💥 Critical startup error: {str(e)}")
        print(f"💥 Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise

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
    try:
        return {
            "status": "healthy",
            "message": "Legal AI Analysis API is operational",
            "timestamp": datetime.now().isoformat(),
            "ai_enabled": gemini_analyzer is not None,
            "version": "3.0.0",
            "environment": {
                "port": os.getenv('PORT', '8000'),
                "python_version": sys.version.split()[0],
                "gemini_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != 'your-gemini-api-key-here')
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/analyze-legal-document")
async def analyze_legal_document(files: List[UploadFile] = File(...)):
    """
    Analyze legal documents with AI and return results immediately.
    No user tracking, no storage - just pure AI analysis.
    
    Returns format: {"clause": "text", "risk": "High/Medium/Low", "laws": "laws", "summary": "summary"}
    """
    import time
    start_time = time.time()
    
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
    
    # Limit number of files to prevent timeout
    if len(files) > 3:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 3 files allowed per request to prevent timeout"
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
                
                # Limit and optimize response size
                max_clauses = 10  # Limit number of clauses
                max_text_length = 500  # Limit text length per clause
                
                # Convert to requested format with size limits
                for i, analysis in enumerate(clause_analyses[:max_clauses]):
                    # Truncate long text fields
                    clause_text = analysis.get("clause", "")[:max_text_length]
                    if len(analysis.get("clause", "")) > max_text_length:
                        clause_text += "..."
                    
                    summary_text = analysis.get("summary", "")[:300]  # Shorter summary
                    if len(analysis.get("summary", "")) > 300:
                        summary_text += "..."
                    
                    laws_text = analysis.get("laws", "")[:200]  # Shorter laws
                    if len(analysis.get("laws", "")) > 200:
                        laws_text += "..."
                    
                    legal_item = {
                        "clause_id": i + 1,
                        "clause": clause_text,
                        "risk": analysis.get("risk", "Medium"),
                        "laws": laws_text,
                        "summary": summary_text
                    }
                    all_legal_analyses.append(legal_item)
                
                processed_files.append(file.filename)
                
            except Exception as e:
                print(f"Error processing {file.filename}: {str(e)}")
                continue
        
        # Return immediate results (no storage) with optimized size
        response_data = {
            "status": "completed",
            "message": f"Successfully analyzed {len(processed_files)} legal documents",
            "files": processed_files,
            "total_documents": len(processed_files),
            "total_clauses_analyzed": len(all_legal_analyses),
            "legal_analysis": all_legal_analyses,
            "analyzed_at": datetime.now().isoformat(),
            "response_info": {
                "max_clauses_per_doc": 10,
                "text_truncated": True,
                "full_analysis_note": "Response optimized for size. Contact for full analysis."
            }
        }
        
        # Log response size for monitoring
        import json
        response_size = len(json.dumps(response_data))
        processing_time = time.time() - start_time
        print(f"📊 Response size: {response_size} bytes ({response_size/1024:.1f} KB)")
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        
        # Add timeout check
        if processing_time > 25:  # Render has 30s timeout
            print("⚠️ Warning: Response approaching timeout limit")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        
    finally:
        # Cleanup temporary files
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/analyze-legal-document-async")
async def analyze_legal_document_async(files: List[UploadFile] = File(...)):
    """
    Start legal document analysis asynchronously.
    Returns job_id immediately, processing happens in background.
    """
    
    # Validate inputs
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    for file in files:
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
    
    # Create job
    job_id = job_manager.create_job("legal_analysis")
    
    # Save files temporarily and store file info
    temp_dir = tempfile.mkdtemp(prefix=f"legal_analysis_{job_id}_")
    file_paths = []
    
    try:
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            file_paths.append(file_path)
        
        # Update job with file info
        job_manager.update_job_progress(job_id, 0, len(files))
        
        # Start background processing
        asyncio.create_task(process_legal_documents_background(
            job_id, file_paths, temp_dir
        ))
        
        return {
            "job_id": job_id,
            "status": "accepted",
            "message": f"Analysis started for {len(files)} files",
            "files": [file.filename for file in files],
            "estimated_time": f"{len(files) * 30-60} seconds",
            "check_status_url": f"/job-status/{job_id}"
        }
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        job_manager.set_job_error(job_id, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status and results of a legal document analysis job.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Return status without result if still processing
    if job["status"] in [JobStatus.PENDING, JobStatus.PROCESSING]:
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "processed_files": job["processed_files"],
            "total_files": job["total_files"],
            "created_at": job["created_at"],
            "started_at": job["started_at"],
            "message": f"Processing... ({job['progress']}% complete)"
        }
    
    # Return full result if completed
    elif job["status"] == JobStatus.COMPLETED:
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": 100,
            "created_at": job["created_at"],
            "started_at": job["started_at"],
            "completed_at": job["completed_at"],
            "result": job["result"]
        }
    
    # Return error if failed
    else:
        return {
            "job_id": job_id,
            "status": job["status"],
            "created_at": job["created_at"],
            "completed_at": job["completed_at"],
            "error": job["error"]
        }

@app.get("/jobs")
async def list_jobs():
    """
    Get summary of all jobs (for debugging/monitoring)
    """
    return {
        "summary": job_manager.get_job_summary(),
        "message": "Job summary retrieved successfully"
    }

async def process_legal_documents_background(job_id: str, file_paths: List[str], temp_dir: str):
    """
    Background task to process legal documents
    """
    try:
        job_manager.update_job_status(job_id, JobStatus.PROCESSING)
        
        all_legal_analyses = []
        processed_files = []
        
        for i, file_path in enumerate(file_paths):
            try:
                print(f"🔄 Processing file {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
                
                # Extract text from PDF
                extracted_text = extract_text_fast(file_path)
                
                if not extracted_text or len(extracted_text.strip()) < 50:
                    print(f"⚠️ Skipping file with insufficient text: {os.path.basename(file_path)}")
                    continue
                
                # Analyze with Gemini AI
                clause_analyses = gemini_analyzer.analyze_legal_document(
                    extracted_text, 
                    "Legal Document"
                )
                
                # Limit and optimize response size
                max_clauses = 10
                max_text_length = 500
                
                for j, analysis in enumerate(clause_analyses[:max_clauses]):
                    clause_text = analysis.get("clause", "")[:max_text_length]
                    if len(analysis.get("clause", "")) > max_text_length:
                        clause_text += "..."
                    
                    summary_text = analysis.get("summary", "")[:300]
                    if len(analysis.get("summary", "")) > 300:
                        summary_text += "..."
                    
                    laws_text = analysis.get("laws", "")[:200]
                    if len(analysis.get("laws", "")) > 200:
                        laws_text += "..."
                    
                    legal_item = {
                        "file": os.path.basename(file_path),
                        "clause_id": j + 1,
                        "clause": clause_text,
                        "risk": analysis.get("risk", "Medium"),
                        "laws": laws_text,
                        "summary": summary_text
                    }
                    all_legal_analyses.append(legal_item)
                
                processed_files.append(os.path.basename(file_path))
                job_manager.update_job_progress(job_id, i + 1, len(file_paths))
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {str(e)}")
                continue
        
        # Prepare final result
        result = {
            "status": "completed",
            "message": f"Successfully analyzed {len(processed_files)} legal documents",
            "files": processed_files,
            "total_documents": len(processed_files),
            "total_clauses_analyzed": len(all_legal_analyses),
            "legal_analysis": all_legal_analyses,
            "analyzed_at": datetime.now().isoformat(),
            "response_info": {
                "max_clauses_per_doc": 10,
                "text_truncated": True,
                "processing_method": "async"
            }
        }
        
        job_manager.set_job_result(job_id, result)
        print(f"✅ Job {job_id} completed successfully")
        
    except Exception as e:
        error_msg = f"Background processing failed: {str(e)}"
        print(f"❌ Job {job_id} failed: {error_msg}")
        job_manager.set_job_error(job_id, error_msg)
        
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/analyze-legal-document-quick")
async def analyze_legal_document_quick(files: List[UploadFile] = File(...)):
    """
    Quick analysis endpoint - returns minimal response for testing
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    if not gemini_analyzer:
        raise HTTPException(status_code=503, detail="AI service unavailable")
    
    # Quick validation and response
    processed_files = []
    for file in files:
        if file.filename and file.filename.lower().endswith('.pdf'):
            processed_files.append(file.filename)
    
    # Minimal response for testing
    return {
        "status": "completed",
        "message": f"Quick analysis of {len(processed_files)} files",
        "files": processed_files,
        "note": "This is a lightweight test endpoint"
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Legal AI Analysis API",
        "version": "4.0.0",
        "status": "operational",
        "ai_enabled": gemini_analyzer is not None,
        "endpoints": [
            "/health - Health check",
            "/analyze-legal-document - Synchronous AI analysis (may timeout)",
            "/analyze-legal-document-async - Asynchronous AI analysis (recommended)",
            "/job-status/{job_id} - Check analysis job status and get results",
            "/jobs - List all jobs summary"
        ],
        "usage": {
            "async_workflow": [
                "1. POST /analyze-legal-document-async with PDF files",
                "2. Get job_id in response",
                "3. Poll GET /job-status/{job_id} until status='completed'",
                "4. Retrieve results from the completed job response"
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
