"""
Job management system for asynchronous legal document analysis
"""

import asyncio
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobManager:
    def __init__(self):
        # In-memory storage for jobs (in production, use Redis or database)
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.max_jobs = 100  # Reduced for cloud deployment
        self.job_timeout = 300  # 5 minutes max per job
        
    def create_job(self, job_type: str = "legal_analysis") -> str:
        """Create a new job and return job ID"""
        job_id = str(uuid.uuid4())[:8]  # Short UUID
        
        # Clean up old jobs if too many
        if len(self.jobs) >= self.max_jobs:
            self._cleanup_old_jobs()
        
        self.jobs[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "status": JobStatus.PENDING,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
            "progress": 0,
            "total_files": 0,
            "processed_files": 0
        }
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID with timeout check"""
        job = self.jobs.get(job_id)
        if job:
            # Check for timeout
            if job["status"] == JobStatus.PROCESSING:
                from datetime import datetime, timedelta
                if job["started_at"]:
                    started = datetime.fromisoformat(job["started_at"])
                    if datetime.now() - started > timedelta(seconds=self.job_timeout):
                        self.set_job_error(job_id, "Job timed out after 5 minutes")
                        job["status"] = JobStatus.FAILED
        return job
    
    def update_job_status(self, job_id: str, status: JobStatus, **kwargs):
        """Update job status and other fields"""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            
            if status == JobStatus.PROCESSING and "started_at" not in self.jobs[job_id]:
                self.jobs[job_id]["started_at"] = datetime.now().isoformat()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                self.jobs[job_id]["completed_at"] = datetime.now().isoformat()
            
            # Update any additional fields
            for key, value in kwargs.items():
                self.jobs[job_id][key] = value
    
    def update_job_progress(self, job_id: str, processed: int, total: int):
        """Update job progress"""
        if job_id in self.jobs:
            self.jobs[job_id]["processed_files"] = processed
            self.jobs[job_id]["total_files"] = total
            self.jobs[job_id]["progress"] = int((processed / total) * 100) if total > 0 else 0
    
    def set_job_result(self, job_id: str, result: Any):
        """Set job result and mark as completed"""
        self.update_job_status(job_id, JobStatus.COMPLETED, result=result)
    
    def set_job_error(self, job_id: str, error: str):
        """Set job error and mark as failed"""
        self.update_job_status(job_id, JobStatus.FAILED, error=error)
    
    def _cleanup_old_jobs(self):
        """Remove oldest completed/failed jobs"""
        # Sort by creation time and remove oldest 20%
        sorted_jobs = sorted(
            [(job_id, job["created_at"]) for job_id, job in self.jobs.items()
             if job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]],
            key=lambda x: x[1]
        )
        
        to_remove = len(sorted_jobs) // 5  # Remove 20%
        for job_id, _ in sorted_jobs[:to_remove]:
            del self.jobs[job_id]
    
    def get_job_summary(self) -> Dict[str, int]:
        """Get summary of all jobs"""
        summary = {status.value: 0 for status in JobStatus}
        for job in self.jobs.values():
            summary[job["status"]] += 1
        summary["total"] = len(self.jobs)
        return summary

# Global job manager instance
job_manager = JobManager()