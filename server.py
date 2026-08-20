"""
TRoyMAR Agent Execution Server
Exposes CrewAI agents as REST endpoints.
Run with: python server.py
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import os
import hmac
import threading
import httpx
from dotenv import load_dotenv
from agency import TRoyMARAgency
from agency.core.memory import shared_memory

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TRoyMAR Agent Server",
    description="Execute CrewAI agents and return results",
    version="1.0.0"
)

BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "")


@app.on_event("shutdown")
def _drain_shared_memory():
    shared_memory.close()


@app.middleware("http")
async def require_backend_key(request: Request, call_next):
    if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
        return await call_next(request)

    if not BACKEND_API_KEY:
        logger.warning("BACKEND_API_KEY is not set — refusing all non-health requests.")
        return JSONResponse(status_code=503, content={"detail": "Server not configured: BACKEND_API_KEY missing"})

    provided = request.headers.get("x-backend-key", "")
    if not hmac.compare_digest(provided, BACKEND_API_KEY):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


agency = TRoyMARAgency()

# ── Request/Response Models ──

class TaskRequest(BaseModel):
    task_id: str
    brief: str
    department: str = ""
    skill: str = ""
    callback_url: str = ""

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: str

# ── Health Check ──

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "TRoyMAR Agent Executor",
        "agency_version": "1.0.0"
    }

@app.get("/status")
def status():
    return agency.status()

# ── Shared Memory (read-only view) ──

@app.get("/memory/records")
def memory_records(limit: int = 100):
    records = shared_memory.list_records()
    records.sort(key=lambda r: r.created_at, reverse=True)
    return {
        "count": len(records),
        "records": [
            {
                "id": r.id,
                "scope": r.scope,
                "categories": r.categories,
                "content": r.content,
                "importance": r.importance,
                "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
            }
            for r in records[:limit]
        ],
    }

# ── Agent Execution ──

def _run_and_callback(task_id: str, department: str, skill: str, brief: str, callback_url: str) -> None:
    try:
        result = route_and_execute(department, skill, brief)
        payload = {"status": "completed", "output": result}
        logger.info(f"Task {task_id} completed successfully")
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        payload = {"status": "failed", "output": str(e)}

    try:
        httpx.post(callback_url, json=payload, headers={"X-Backend-Key": BACKEND_API_KEY}, timeout=30)
    except Exception as e:
        logger.error(f"Task {task_id}: callback to {callback_url} failed: {str(e)}")


@app.post("/execute", response_model=TaskResponse)
def execute_task(request: TaskRequest) -> TaskResponse:
    if request.callback_url:
        thread = threading.Thread(
            target=_run_and_callback,
            args=(request.task_id, request.department, request.skill, request.brief, request.callback_url),
            daemon=True,
        )
        thread.start()
        return TaskResponse(task_id=request.task_id, status="accepted", result="")

    try:
        logger.info(f"Executing task {request.task_id}: {request.department}.{request.skill}")
        result = route_and_execute(request.department, request.skill, request.brief)
        logger.info(f"Task {request.task_id} completed successfully")
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        logger.error(f"Task {request.task_id} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Orchestrator ──

@app.post("/orchestrate", response_model=TaskResponse)
def orchestrate_brief(request: TaskRequest) -> TaskResponse:
    try:
        logger.info(f"Orchestrating brief {request.task_id}")
        result = agency.intake_brief(request.brief)
        logger.info(f"Orchestration {request.task_id} completed")
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        logger.error(f"Orchestration {request.task_id} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Department-Specific Endpoints ──

@app.post("/marketing/port-call-intel", response_model=TaskResponse)
def marketing_port_call_intel(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.marketing.port_call_intel(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/marketing/capability-content", response_model=TaskResponse)
def marketing_capability_content(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.marketing.capability_content(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/marketing/reputation-audit", response_model=TaskResponse)
def marketing_reputation_audit(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.marketing.reputation_audit(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sales/agency-appointment", response_model=TaskResponse)
def sales_agency_appointment(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.sales.agency_appointment(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sales/brokerage", response_model=TaskResponse)
def sales_brokerage(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.sales.brokerage(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sales/outreach", response_model=TaskResponse)
def sales_outreach(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.sales.outreach(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sales/find-opportunities", response_model=TaskResponse)
def sales_find_opportunities(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.sales.find_opportunities(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sales/objection-handler", response_model=TaskResponse)
def sales_objection_handler(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.sales.objection_handler(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finance/disbursement-account", response_model=TaskResponse)
def finance_disbursement_account(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.finance.disbursement_account(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finance/billing-flow", response_model=TaskResponse)
def finance_billing_flow(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.finance.billing_flow(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finance/reporting", response_model=TaskResponse)
def finance_reporting(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.finance.reporting(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/operations/sub-agent-network", response_model=TaskResponse)
def operations_sub_agent_network(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.shipping.sub_agent_network(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/operations/port-call-logistics", response_model=TaskResponse)
def operations_port_call_logistics(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.shipping.port_call_logistics(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/operations/husbandry-coordination", response_model=TaskResponse)
def operations_husbandry_coordination(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.shipping.husbandry_coordination(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/operations/tool-integration", response_model=TaskResponse)
def operations_tool_integration(request: TaskRequest) -> TaskResponse:
    try:
        result = agency.shipping.tool_integration(request.brief)
        return TaskResponse(task_id=request.task_id, status="completed", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Helper function ──

def route_and_execute(department: str, skill: str, brief: str) -> str:
    department = department.lower()
    skill = skill.lower()

    routes = {
        "orchestrator": {
            "intake_brief": agency.intake_brief,
        },
        "shipping": {
            "daily_briefing": agency.run_daily_briefing,
            "sub_agent_network": agency.shipping.sub_agent_network,
            "port_call_logistics": agency.shipping.port_call_logistics,
            "husbandry_coordination": agency.shipping.husbandry_coordination,
            "tool_integration": agency.shipping.tool_integration,
            "run_task": agency.shipping.run_task,
        },
        "marketing": {
            "port_call_intel": agency.marketing.port_call_intel,
            "capability_content": agency.marketing.capability_content,
            "reputation_audit": agency.marketing.reputation_audit,
            "run_campaign": agency.marketing.run_campaign,
        },
        "sales": {
            "agency_appointment": agency.sales.agency_appointment,
            "brokerage": agency.sales.brokerage,
            "outreach": agency.sales.outreach,
            "objection_handler": agency.sales.objection_handler,
            "run_pipeline": agency.sales.run_pipeline,
            "find_opportunities": agency.sales.find_opportunities,
        },
        "finance": {
            "disbursement_account": agency.finance.disbursement_account,
            "billing_flow": agency.finance.billing_flow,
            "reporting": agency.finance.reporting,
            "generate_report": agency.finance.generate_report,
        },
    }

    handler = routes.get(department, {}).get(skill)
    if handler is None:
        raise ValueError(f"Unknown department/skill: {department}/{skill}")
    return handler(brief)

# ── Main ──

if __name__ == "__main__":
    import sys
    import uvicorn

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    print("========================================================")
    print("       TRoyMAR Agent Execution Server")
    print("       Starting at http://localhost:8100")
    print("       API docs at http://localhost:8100/docs")
    print("========================================================")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8100,
        log_level="info"
    )
