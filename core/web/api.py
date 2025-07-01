"""
FastAPI server for DBA-GPT
"""

import asyncio
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from core.ai.dba_assistant import DBAAssistant
from core.utils.logger import setup_logger

logger = setup_logger(__name__)


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    database: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    recommendation: Dict[str, Any]


class DatabaseStatus(BaseModel):
    name: str
    type: str
    status: str
    metrics: Dict[str, Any]


class AnalysisRequest(BaseModel):
    database: str
    analysis_type: str


class AnalysisResponse(BaseModel):
    database: str
    analysis_type: str
    results: Dict[str, Any]


# FastAPI app
app = FastAPI(
    title="DBA-GPT API",
    description="AI-Powered Database Administration API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global assistant instance
assistant: Optional[DBAAssistant] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the assistant on startup"""
    global assistant
    # This would be initialized by the main application
    logger.info("DBA-GPT API server starting...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DBA-GPT API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with DBA-GPT"""
    try:
        if not assistant:
            raise HTTPException(status_code=503, detail="Assistant not initialized")
            
        # Get AI recommendation
        recommendation = await assistant.get_recommendation(
            request.message, 
            request.database
        )
        
        # Format response
        response = f"""
Issue: {recommendation.issue}
Severity: {recommendation.severity}
Category: {recommendation.category}

Description: {recommendation.description}

Solution: {recommendation.solution}

Estimated Impact: {recommendation.estimated_impact}
Risk Level: {recommendation.risk_level}
        """
        
        if recommendation.sql_commands:
            response += "\n\nSQL Commands:\n"
            for i, cmd in enumerate(recommendation.sql_commands, 1):
                response += f"{i}. {cmd}\n"
                
        return ChatResponse(
            response=response.strip(),
            recommendation={
                "issue": recommendation.issue,
                "severity": recommendation.severity,
                "description": recommendation.description,
                "solution": recommendation.solution,
                "sql_commands": recommendation.sql_commands,
                "estimated_impact": recommendation.estimated_impact,
                "risk_level": recommendation.risk_level,
                "category": recommendation.category
            }
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/databases", response_model=List[DatabaseStatus])
async def get_databases():
    """Get list of configured databases"""
    try:
        if not assistant:
            raise HTTPException(status_code=503, detail="Assistant not initialized")
            
        databases = []
        for db_name, db_config in assistant.config.databases.items():
            # Get basic status (in a real implementation, this would check connectivity)
            databases.append(DatabaseStatus(
                name=db_name,
                type=db_config.db_type,
                status="configured",
                metrics={
                    "host": db_config.host,
                    "port": db_config.port,
                    "database": db_config.database
                }
            ))
            
        return databases
        
    except Exception as e:
        logger.error(f"Error getting databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/databases/{db_name}/status")
async def get_database_status(db_name: str):
    """Get status of a specific database"""
    try:
        if not assistant:
            raise HTTPException(status_code=503, detail="Assistant not initialized")
            
        db_config = assistant.config.get_database_config(db_name)
        if not db_config:
            raise HTTPException(status_code=404, detail=f"Database {db_name} not found")
            
        # Get database metrics
        metrics = await assistant.analyzer.get_current_metrics(db_config)
        health = await assistant.analyzer.get_system_health(db_config)
        
        return {
            "database": db_name,
            "type": db_config.db_type,
            "status": "connected" if "error" not in metrics else "error",
            "metrics": metrics,
            "health": health,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_database(request: AnalysisRequest):
    """Analyze a specific database"""
    try:
        if not assistant:
            raise HTTPException(status_code=503, detail="Assistant not initialized")
            
        db_config = assistant.config.get_database_config(request.database)
        if not db_config:
            raise HTTPException(status_code=404, detail=f"Database {request.database} not found")
            
        # Generate performance report
        report = await assistant.analyzer.generate_performance_report(db_config)
        
        return AnalysisResponse(
            database=request.database,
            analysis_type=request.analysis_type,
            results=report
        )
        
    except Exception as e:
        logger.error(f"Error analyzing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tips")
async def get_tips(database_type: Optional[str] = None):
    """Get DBA tips"""
    try:
        if not assistant:
            raise HTTPException(status_code=503, detail="Assistant not initialized")
            
        tips = await assistant.get_quick_tips(database_type)
        
        return {
            "tips": tips,
            "database_type": database_type,
            "count": len(tips)
        }
        
    except Exception as e:
        logger.error(f"Error getting tips: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """Get current configuration"""
    try:
        if not assistant:
            raise HTTPException(status_code=503, detail="Assistant not initialized")
            
        return {
            "ai": {
                "model": assistant.config.ai.model,
                "temperature": assistant.config.ai.temperature,
                "max_tokens": assistant.config.ai.max_tokens
            },
            "monitoring": {
                "enabled": assistant.config.monitoring.enabled,
                "interval": assistant.config.monitoring.interval,
                "auto_remediation": assistant.config.monitoring.auto_remediation
            },
            "databases": {
                name: {
                    "type": config.db_type,
                    "host": config.host,
                    "port": config.port,
                    "database": config.database
                }
                for name, config in assistant.config.databases.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/monitor/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start database monitoring"""
    try:
        if not assistant:
            raise HTTPException(status_code=503, detail="Assistant not initialized")
            
        # This would start the monitoring system
        background_tasks.add_task(start_monitoring_task)
        
        return {"message": "Monitoring started", "status": "running"}
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/monitor/stop")
async def stop_monitoring():
    """Stop database monitoring"""
    try:
        # This would stop the monitoring system
        return {"message": "Monitoring stopped", "status": "stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitor/status")
async def get_monitoring_status():
    """Get monitoring status"""
    try:
        # This would get the actual monitoring status
        return {
            "status": "running",
            "databases_monitored": len(assistant.config.databases) if assistant else 0,
            "last_check": asyncio.get_event_loop().time(),
            "alerts": []
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def start_monitoring_task():
    """Background task to start monitoring"""
    try:
        logger.info("Starting monitoring task...")
        # This would start the actual monitoring
        await asyncio.sleep(1)  # Placeholder
        logger.info("Monitoring task started")
    except Exception as e:
        logger.error(f"Error in monitoring task: {e}")


async def start_api_server(assistant_instance: DBAAssistant, host: str = "0.0.0.0", port: int = 8000):
    """Start the API server"""
    global assistant
    assistant = assistant_instance
    
    logger.info(f"Starting DBA-GPT API server on {host}:{port}")
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # For direct execution
    uvicorn.run(app, host="0.0.0.0", port=8000) 