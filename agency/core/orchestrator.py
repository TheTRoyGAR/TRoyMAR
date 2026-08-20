from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel

from agency.core.llm import get_llm
from agency.core.memory import shared_memory, remember, recall_context


class DelegationPlan(BaseModel):
    plan: str
    needs_clarification: list[str] = []


class CoreOrchestrator:
    """CEO Assistant — intakes port-call/client briefs, delegates, reviews, and QA's deliverables."""

    def __init__(self, agency):
        self.agency = agency

        self.ceo_assistant = Agent(
            role="CEO Assistant and Lead Operations Agent",
            goal=(
                "Intake port-call and client briefs, define agency strategy, delegate work to "
                "department heads, and ensure every deliverable is production-ready before it "
                "reaches a ship owner, operator, or charterer."
            ),
            backstory=(
                "You are the CEO Assistant and Lead Operations Agent for TRoy Maritime Agency "
                "(TRoyMAR) — a ship agency, husbandry, and maritime logistics company owned by "
                "CEO I. Ertan Govdeli, who has real prior experience as a ship agent handling "
                "vessels transiting the Dardanelles and Bosphorus at Istanbul. "
                "Your job is to intake briefs — a new port call, a client business-development "
                "target, an internal task — define the overall strategy, and break the work down "
                "into tasks for your 4 department heads: Marketing, Sales, Finance, and "
                "Shipping & Ship Agency Operations.\n\n"
                "You possess three core skills:\n"
                "1. DELEGATE — Assign tasks to specific departmental agents with clear, scoped instructions.\n"
                "2. REVIEW — Evaluate department outputs against the original brief, "
                "checking for completeness, accuracy, and quality.\n"
                "3. FINAL_QA — Ensure all deliverables are production-ready before delivery. "
                "Check formatting, consistency, and that every requirement in the brief is addressed.\n\n"
                "Never guess data — a wrong port fact, a wrong vessel detail, or an invented price "
                "can cost a real ship real money and real time in port. If an agent needs missing "
                "context, instruct them to ask. Nothing leaves the agency without your sign-off."
            ),
            llm=get_llm("opus"),
            verbose=True,
            allow_delegation=True,
        )

    # ── DELEGATE ──────────────────────────────────────────────────────────────

    def _decompose(self, client_brief: str) -> DelegationPlan:
        task = Task(
            description=(
                f"{recall_context(client_brief)}"
                f"A new brief has arrived. Analyze it carefully and produce a delegation plan "
                f"that specifies exactly what each department must deliver.\n\n"
                f"BRIEF:\n{client_brief}\n\n"
                "Never guess data. If the brief is missing information a department genuinely "
                "needs to do real work (e.g. no vessel/port details, no target operator, no "
                "budget, no timeline when one matters), list each specific missing item in "
                "needs_clarification instead of inventing an assumption for it. Only put items "
                "there that would actually block real, useful work — not every nice-to-have."
            ),
            expected_output=(
                "plan: DELEGATION PLAN — one section per department needed:\n"
                "MARKETING: [specific deliverable]\n"
                "SALES: [specific deliverable]\n"
                "FINANCE: [specific deliverable]\n"
                "SHIPPING: [specific deliverable]\n"
                "Include priority order and any cross-department dependencies.\n\n"
                "needs_clarification: list of specific missing-info questions to ask, "
                "empty list if the brief has everything needed."
            ),
            agent=self.ceo_assistant,
            output_pydantic=DelegationPlan,
        )
        crew = Crew(
            agents=[self.ceo_assistant],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        crew.kickoff()
        return task.output.pydantic

    def _route_departments(self, brief: str, plan: str) -> dict:
        combined = (brief + " " + plan).lower()
        results = {}

        marketing_keys = ["market", "content", "campaign", "social", "brand", "seo", "reputation", "trend"]
        sales_keys = ["sales", "lead", "pipeline", "prospect", "appointment", "outreach", "close", "deal", "operator", "charterer"]
        finance_keys = ["finance", "roi", "cost", "revenue", "invoice", "billing", "budget", "report", "disbursement", "da "]
        ops_keys = ["port call", "berth", "husbandry", "customs", "logistics", "chandlery", "spare", "vessel", "shipping", "workflow", "system", "tool", "integrat"]

        if any(k in combined for k in marketing_keys):
            results["Marketing"] = self.agency.marketing.run_campaign(brief)
        if any(k in combined for k in sales_keys):
            results["Sales"] = self.agency.sales.run_pipeline(brief)
        if any(k in combined for k in finance_keys):
            results["Finance"] = self.agency.finance.generate_report("project")
        if any(k in combined for k in ops_keys):
            results["Shipping"] = self.agency.shipping.run_task(brief)

        # Default: all departments if no keyword matched
        if not results:
            results["Marketing"] = self.agency.marketing.run_campaign(brief)
            results["Sales"] = self.agency.sales.run_pipeline(brief)
            results["Finance"] = self.agency.finance.generate_report("project")
            results["Shipping"] = self.agency.shipping.run_task(brief)

        return results

    # ── REVIEW + FINAL_QA ─────────────────────────────────────────────────────

    def _review_and_qa(self, client_brief: str, dept_results: dict) -> str:
        collected = "\n\n".join(
            f"=== {dept} OUTPUT ===\n{output}"
            for dept, output in dept_results.items()
        )

        task_review = Task(
            description=(
                f"REVIEW all department outputs against the original brief.\n\n"
                f"ORIGINAL BRIEF:\n{client_brief}\n\n"
                f"DEPARTMENT OUTPUTS:\n{collected}\n\n"
                "Evaluate: completeness, accuracy, quality, alignment with brief requirements."
            ),
            expected_output=(
                "REVIEW REPORT:\n"
                "- Overall quality score (1-10)\n"
                "- Per-department assessment (1-2 lines each)\n"
                "- Any missing elements\n"
                "- Ready for FINAL_QA: YES / NO + reason"
            ),
            agent=self.ceo_assistant,
        )

        task_qa = Task(
            description=(
                "FINAL_QA — compile the production-ready deliverable package. "
                "Incorporate your review findings. Organize all outputs professionally, "
                "address any gaps, and format for direct delivery."
            ),
            expected_output=(
                "DELIVERABLE PACKAGE\n"
                "Professional, complete, formatted package ready to send. "
                "All department outputs organized by section."
            ),
            agent=self.ceo_assistant,
            context=[task_review],
        )

        crew = Crew(
            agents=[self.ceo_assistant],
            tasks=[task_review, task_qa],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        return str(crew.kickoff())

    # ── PUBLIC ENTRY POINT ────────────────────────────────────────────────────

    def intake_brief(self, client_brief: str) -> str:
        """Full orchestration: DELEGATE → collect → REVIEW → FINAL_QA.

        Hard Python gate, not just an LLM instruction: if _decompose flags
        needs_clarification, work stops here and the questions go back to
        the requester — no department runs on guessed data.
        """
        delegation = self._decompose(client_brief)
        if delegation.needs_clarification:
            questions = "\n".join(f"- {q}" for q in delegation.needs_clarification)
            remember(
                f"Brief '{client_brief}' needs clarification before work can start:\n{questions}",
                scope="/orchestrator/intake_brief",
                categories=["orchestrator", "brief", "needs_clarification"],
            )
            return (
                "Before I can delegate this to the departments, I need a bit more information:\n\n"
                f"{questions}\n\n"
                "No department work has started yet — send these details and I'll proceed."
            )

        dept_results = self._route_departments(client_brief, delegation.plan)
        final_package = self._review_and_qa(client_brief, dept_results)
        remember(
            f"Full orchestration for brief '{client_brief}':\n{final_package}",
            scope="/orchestrator/intake_brief",
            categories=["orchestrator", "brief"],
            importance=0.7,
        )
        return final_package
