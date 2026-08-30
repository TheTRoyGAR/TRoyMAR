from crewai import Agent, Task, Crew, Process
from agency.core.llm import get_llm
from agency.core.memory import shared_memory, remember, recall_context
from agency.tools import write


class FinanceDepartment:
    """Finance Department — 1 head + 4 specialists. Skills: DISBURSEMENT_ACCOUNT, BILLING_FLOW, REPORTING."""

    def __init__(self):
        llm = get_llm("haiku")

        self.finance_head = Agent(
            role="Head of the AI Finance Department",
            goal=(
                "Track real port-call costs and TRoyMAR's own margins, produce accurate "
                "Disbursement Accounts for clients, and automate billing so the agency's cash "
                "flow stays healthy."
            ),
            backstory=(
                "You are the Head of the AI Finance Department at TRoy Maritime Agency (TRoyMAR). "
                "In ship agency, the core financial deliverable is the Disbursement Account (DA) — "
                "an itemized statement of every real port cost (pilotage, tugs, berth dues, "
                "customs, husbandry) plus the agency fee, sent to the ship owner/operator after a "
                "call. Your goal is to keep these accurate and prompt, track TRoyMAR's own real "
                "margins, and automate billing.\n\n"
                "You possess three core skills:\n"
                "1. DISBURSEMENT_ACCOUNT — Build an itemized, accurate port-call cost statement "
                "(real cost categories, never invented line items or amounts) plus TRoyMAR's "
                "agency fee, clearly separated.\n"
                "2. BILLING_FLOW — Map out automated invoicing, DA delivery, and payment-failure "
                "follow-up workflows.\n"
                "3. REPORTING — Generate client-facing financial summary reports showing real "
                "costs, margins, and cash flow.\n\n"
                "All financial models must be transparent, defensible, and based on stated "
                "assumptions — a wrong number in a DA is a real, disputable client problem.\n\n"
                "Operating rules: split CONFIRMED (real published port tariffs, agency fee "
                "schedules) from ESTIMATED clearly, every time. Never fabricate a disbursement "
                "account balance or a client's payment status. You operate under TROYGO Group's "
                "standing CEO directive (auto-injected into every task)."
            ),
            llm=llm,
            tools=[write],
            verbose=False,
        )

        self.da_clerk = Agent(
            role="Disbursement Account Clerk",
            goal="Compile accurate, itemized Disbursement Accounts for real port calls.",
            backstory=(
                "You are the Disbursement Account Clerk at TRoy Maritime Agency. You itemize real "
                "port costs — pilotage, tugs, berth dues, customs, husbandry expenses — into a "
                "clean, accurate DA. Never invent a cost category or amount not actually stated."
            ),
            llm=llm,
            verbose=False,
        )

        self.budget_planner = Agent(
            role="Budget Planner",
            goal="Create and maintain monthly and quarterly budgets for TRoyMAR.",
            backstory=(
                "You are the Budget Planner at TRoy Maritime Agency. You analyze real spending "
                "patterns, forecast revenue from confirmed/likely agency appointments, and build "
                "budgets that keep the agency profitable."
            ),
            llm=llm,
            verbose=False,
        )

        self.invoice_manager = Agent(
            role="Invoice Manager",
            goal="Create, send, and track all client invoices and DA payments.",
            backstory=(
                "You are the Invoice Manager at TRoy Maritime Agency. You manage the full "
                "invoicing lifecycle for agency fees and Disbursement Accounts — creation through "
                "payment-failure follow-up and reconciliation."
            ),
            llm=llm,
            tools=[write],
            verbose=False,
        )

        self.cost_optimizer = Agent(
            role="Cost Optimizer",
            goal="Identify real cost-saving opportunities without compromising service quality.",
            backstory=(
                "You are the Cost Optimizer at TRoy Maritime Agency. You look for real ways to "
                "reduce operating costs and improve TRoyMAR's own margins on each port call, "
                "without cutting corners on real port services."
            ),
            llm=llm,
            verbose=False,
        )

    # ── SKILL: DISBURSEMENT_ACCOUNT ───────────────────────────────────────────────

    def disbursement_account(self, port_call_brief: str) -> str:
        task = Task(
            description=(
                f"{recall_context(port_call_brief)}"
                f"DISBURSEMENT_ACCOUNT: Build an itemized Disbursement Account for this port "
                f"call: {port_call_brief}\n\n"
                "List real cost categories (pilotage, tugs, berth dues, customs, husbandry, other "
                "port charges as applicable) plus TRoyMAR's agency fee, clearly separated. If real "
                "amounts aren't provided, use clearly-labeled placeholder ranges rather than "
                "inventing specific figures — state all assumptions explicitly."
            ),
            expected_output=(
                "## Disbursement Account\n"
                "**Vessel/Call Details** — as given\n"
                "**Itemized Port Costs** — category, description, amount (or placeholder range + assumption)\n"
                "**Agency Fee** — clearly separated\n"
                "**Total**\n"
                "**Assumptions** — listed explicitly wherever a real figure wasn't provided"
            ),
            agent=self.da_clerk,
        )
        crew = Crew(
            agents=[self.da_clerk],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Finance DISBURSEMENT_ACCOUNT for '{port_call_brief}':\n{result}",
            scope="/dept/finance/disbursement_account",
            categories=["finance", "disbursement_account"],
        )
        return result

    # ── SKILL: BILLING_FLOW ───────────────────────────────────────────────────────

    def billing_flow(self, client: str) -> str:
        task = Task(
            description=(
                f"{recall_context(client)}"
                f"BILLING_FLOW: Design a complete automated billing workflow for: {client}\n\n"
                "Include: DA/invoice delivery triggers, payment reminders, and payment-failure "
                "escalation steps."
            ),
            expected_output=(
                "## Automated Billing Workflow\n"
                "**Delivery Triggers** — what events create/send a DA or invoice\n"
                "**Reminder Sequence** — Day 1, Day 7, Day 14 reminders\n"
                "**Payment Failure Flow** — escalation steps with templates\n"
                "**Tools Required** — recommended stack"
            ),
            agent=self.finance_head,
        )
        task_invoice = Task(
            description="Write the 3 payment reminder templates referenced in the billing flow.",
            expected_output="3 templates: Day 1 (friendly), Day 7 (firm), Day 14 (final notice). Subject + body each.",
            agent=self.invoice_manager,
            context=[task],
        )
        crew = Crew(
            agents=[self.finance_head, self.invoice_manager],
            tasks=[task, task_invoice],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        crew_output = crew.kickoff()
        result = (
            f"{str(crew_output.tasks_output[0])}\n\n---\n\n{str(crew_output.tasks_output[1])}"
            if len(crew_output.tasks_output) >= 2
            else str(crew_output)
        )
        remember(
            f"Finance BILLING_FLOW for client '{client}':\n{result}",
            scope="/dept/finance/billing_flow",
            categories=["finance", "billing"],
        )
        return result

    # ── SKILL: REPORTING ──────────────────────────────────────────────────────────

    def reporting(self, period: str = "monthly") -> str:
        task_books = Task(
            description=f"Summarize the {period} financial transactions and categorize income vs expenses.",
            expected_output="Categorized summary: revenue streams (agency fees), expense categories, net position.",
            agent=self.budget_planner,
        )
        task_report = Task(
            description=(
                f"REPORTING: Generate a {period} client-facing financial summary report "
                "using the budget planner's summary."
            ),
            expected_output=(
                "## Financial Summary Report\n"
                "**Revenue** — breakdown by stream\n"
                "**Expenses** — breakdown by category\n"
                "**Profit Margin** — %\n"
                "**Cash Flow** — net position\n"
                "**Key Insights** — 3 bullet points\n"
                "**Recommendations** — 2 actions for next period"
            ),
            agent=self.finance_head,
            context=[task_books],
        )
        crew = Crew(
            agents=[self.budget_planner, self.finance_head],
            tasks=[task_books, task_report],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Finance REPORTING ({period}):\n{result}",
            scope="/dept/finance/reporting",
            categories=["finance", "reporting"],
        )
        return result

    def generate_report(self, period: str = "monthly") -> str:
        task_report = Task(
            description=(
                f"Generate a {period} financial report for TRoy Maritime Agency. "
                "Include: revenue summary (agency fees), expense categories, profit margin, cash flow."
            ),
            expected_output=(
                "Financial report with sections: REVENUE, EXPENSES, PROFIT MARGIN, "
                "CASH FLOW, KEY INSIGHTS. Use placeholder numbers if no real data provided."
            ),
            agent=self.finance_head,
        )
        task_optimize = Task(
            description="Based on the financial report, identify 3 real cost-saving opportunities.",
            expected_output="3 specific cost-saving actions with estimated savings per month.",
            agent=self.cost_optimizer,
            context=[task_report],
        )
        crew = Crew(
            agents=[self.finance_head, self.cost_optimizer],
            tasks=[task_report, task_optimize],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Finance report ({period}):\n{result}",
            scope="/dept/finance/generate_report",
            categories=["finance", "reporting"],
        )
        return result
