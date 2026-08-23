from agency.departments.marketing import MarketingDepartment
from agency.departments.sales import SalesDepartment
from agency.departments.finance import FinanceDepartment
from agency.departments.operations import ShippingDepartment


class TRoyMARAgency:
    """TRoy Maritime Agency (TRoyMAR) — Core Orchestrator + 4 departments, 21 agents, zero employees."""

    CEO = "I. Ertan Govdeli"
    NAME = "TRoy Maritime Agency (TRoyMAR)"

    def __init__(self):
        self.marketing = MarketingDepartment()
        self.sales = SalesDepartment()
        self.finance = FinanceDepartment()
        self.shipping = ShippingDepartment()

        # Orchestrator last — it holds a reference to self
        from agency.core.orchestrator import CoreOrchestrator
        self.orchestrator = CoreOrchestrator(self)

    # ── ORCHESTRATOR ──────────────────────────────────────────────────────────

    def intake_brief(self, brief: str) -> str:
        """CEO Assistant: DELEGATE → collect → REVIEW → FINAL_QA."""
        return self.orchestrator.intake_brief(brief)

    # ── DEPARTMENT SHORTCUTS ──────────────────────────────────────────────────

    def run_daily_briefing(self, context: str = "") -> str:
        return self.shipping.daily_briefing(context)

    def run_sales_pipeline(self, brief: str) -> str:
        return self.sales.run_pipeline(brief)

    def run_marketing_campaign(self, brief: str) -> str:
        return self.marketing.run_campaign(brief)

    def run_finance_report(self, period: str = "monthly") -> str:
        return self.finance.generate_report(period)

    def run_operations_task(self, brief: str) -> str:
        return self.shipping.run_task(brief)

    # ── STATUS ────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "agency": self.NAME,
            "ceo": self.CEO,
            "orchestrator": {
                "agent": "CEO Assistant",
                "skills": ["DELEGATE", "REVIEW", "FINAL_QA"],
            },
            "departments": 4,
            "agents_per_department": "5 (Shipping has 6)",
            "total_agents": 22,
            "department_skills": {
                "marketing": ["PORT_CALL_INTEL", "CAPABILITY_CONTENT", "REPUTATION_AUDIT"],
                "sales": ["AGENCY_APPOINTMENT", "BROKERAGE", "OUTREACH", "OBJECTION_HANDLER", "FIND_OPPORTUNITIES"],
                "finance": ["DISBURSEMENT_ACCOUNT", "BILLING_FLOW", "REPORTING"],
                "shipping": ["SUB_AGENT_NETWORK", "PORT_CALL_LOGISTICS", "HUSBANDRY_COORDINATION", "TOOL_INTEGRATION", "CARGO_LOGISTICS_MANAGEMENT"],
            },
            "shared_memory": "all departments read/write one cross-department knowledge store (agency/core/memory.py)",
            "status": "online",
        }
