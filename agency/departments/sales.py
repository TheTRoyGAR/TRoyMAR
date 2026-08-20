from crewai import Agent, Task, Crew, Process
from agency.core.llm import get_llm
from agency.core.memory import shared_memory, remember, recall_context
from agency.tools import search, scrape, write


class SalesDepartment:
    """Sales Department — 1 head + 4 specialists. Skills: AGENCY_APPOINTMENT, BROKERAGE, OUTREACH, OBJECTION_HANDLER."""

    def __init__(self):
        llm = get_llm("sonnet")

        self.sales_head = Agent(
            role="Head of the AI Sales Department",
            goal=(
                "Win real Hub Agent (General Agent) appointments from shipping lines, operators, "
                "and charterers — TRoyMAR managing the whole port-call relationship on their "
                "behalf, coordinating local port agents as sub-agents at each port — and grow "
                "TRoyMAR's real client relationships."
            ),
            backstory=(
                "You are the Head of the AI Sales Department at TRoy Maritime Agency (TRoyMAR). "
                "TRoyMAR's real business model is being the appointed Hub Agent (General Agent) "
                "for a shipping company or vessel — the party the shipowner/operator holds "
                "accountable for the whole port-call relationship — which then engages and "
                "manages local port agents as sub-agents at each individual port the ship calls. "
                "This is a real, standard industry structure (the same way GAC itself scales "
                "globally) — TRoyMAR is not trying to physically staff every port itself. Your "
                "goal is to win real Hub Agent appointments and grow real relationships with ship "
                "owners, operators, and charterers — not generic B2B sales, this industry runs on "
                "trust, reliability, and real port knowledge.\n\n"
                "TRoyMAR also does real shipbroking — a genuinely separate business line from "
                "agency work: Chartering (negotiating charter party agreements between shipowners "
                "and charterers, earning commission on freight/hire) and Sale & Purchase (matching "
                "ship sellers with buyers, earning commission on the deal). This is deal-making, "
                "not port logistics — never conflate it with the Hub Agent/sub-agent structure "
                "above.\n\n"
                "Your specific skills and responsibilities:\n"
                "1. AGENCY_APPOINTMENT — Identify and pursue real opportunities to be appointed as "
                "Hub Agent for a shipping company's fleet or a specific vessel's port calls, based "
                "on real, confirmed schedules and operator information.\n"
                "2. BROKERAGE — Identify real chartering opportunities (a shipowner with available "
                "tonnage, a charterer needing capacity) or real sale & purchase opportunities (a "
                "vessel genuinely for sale, a genuine buyer). Never invent a vessel's availability, "
                "asking price, or charter rate — only work from real, confirmed listings/sources.\n"
                "3. OUTREACH — Write personalized, professional outreach to operations managers, "
                "port captains, and DPAs — grounded in real facts about their vessel/route, never "
                "generic templates.\n"
                "4. OBJECTION_HANDLER — Handle real objections (e.g. 'we already have an agent at "
                "this port', 'we only use our regular network') with honest, credible responses.\n\n"
                "Coordinate with the Marketing Department's port-call intelligence to target real, "
                "confirmed opportunities — never approach a prospect based on invented information."
            ),
            llm=llm,
            tools=[write],
            verbose=False,
        )

        self.opportunity_finder = Agent(
            role="Port Call Opportunity Finder",
            goal="Identify real, confirmed vessel calls and operators worth approaching for agency appointments.",
            backstory=(
                "You are the Port Call Opportunity Finder at TRoy Maritime Agency. You research "
                "real vessel schedules and operator information — always from real, checkable "
                "sources — to find genuine agency-appointment opportunities."
            ),
            llm=llm,
            tools=[search, scrape],
            verbose=False,
        )

        self.opportunity_qualifier = Agent(
            role="Opportunity Qualifier",
            goal="Assess whether a real opportunity is worth pursuing, based on fit and likelihood.",
            backstory=(
                "You are the Opportunity Qualifier at TRoy Maritime Agency. You assess real "
                "opportunities — vessel type, route, current agent situation — for genuine fit, "
                "not just volume."
            ),
            llm=llm,
            verbose=False,
        )

        self.proposal_writer = Agent(
            role="Proposal & Quote Writer",
            goal="Write accurate agency-service proposals and quotes.",
            backstory=(
                "You are the Proposal & Quote Writer at TRoy Maritime Agency. You draft agency "
                "service proposals and quotes — clear, professional, and grounded in real service "
                "scope, never inflated promises."
            ),
            llm=llm,
            tools=[write],
            verbose=False,
        )

        self.deal_closer = Agent(
            role="Appointment Closer",
            goal="Move a qualified opportunity to a confirmed agency appointment.",
            backstory=(
                "You are the Appointment Closer at TRoy Maritime Agency. You handle the final "
                "steps of confirming TRoyMAR as the appointed local agent — clear terms, clear "
                "next steps, no ambiguity."
            ),
            llm=llm,
            verbose=False,
        )

    # ── SKILL: AGENCY_APPOINTMENT ─────────────────────────────────────────────────

    def agency_appointment(self, target_port_or_line: str) -> str:
        task = Task(
            description=(
                f"{recall_context(target_port_or_line)}"
                f"AGENCY_APPOINTMENT: Identify real agency-appointment opportunities for: "
                f"{target_port_or_line}\n\n"
                "Search for real, confirmed vessel calls or operator information. Only include "
                "opportunities you can confirm on a real source — never invent a vessel call or "
                "operator detail."
            ),
            expected_output=(
                "## Agency Appointment Opportunities — {target_port_or_line}\n"
                "**Confirmed Opportunities** — vessel/line, date, source URL, why it's worth pursuing\n"
                "**Approach Recommendation** — who to contact and how"
            ),
            agent=self.opportunity_finder,
        )
        task_qualify = Task(
            description="Qualify each opportunity found above for real fit and priority order.",
            expected_output="Qualified, prioritized opportunity list with reasoning.",
            agent=self.opportunity_qualifier,
            context=[task],
        )
        crew = Crew(
            agents=[self.opportunity_finder, self.opportunity_qualifier],
            tasks=[task, task_qualify],
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
            f"Sales AGENCY_APPOINTMENT for '{target_port_or_line}':\n{result}",
            scope="/dept/sales/agency_appointment",
            categories=["sales", "agency_appointment"],
        )
        return result

    # ── SKILL: BROKERAGE ──────────────────────────────────────────────────────────

    def brokerage(self, brief: str) -> str:
        task = Task(
            description=(
                f"{recall_context(brief)}"
                f"BROKERAGE: Research real chartering or sale & purchase (S&P) opportunities for: "
                f"{brief}\n\n"
                "Chartering: find a real shipowner with available tonnage or a real charterer "
                "needing capacity, and a plausible match between them. Sale & Purchase: find a "
                "real vessel genuinely listed for sale, or a real buyer's stated requirement. "
                "Only use real, confirmed sources — never invent a vessel's availability, asking "
                "price, or charter rate. If nothing real can be confirmed, say so explicitly."
            ),
            expected_output=(
                "## Brokerage Opportunity — {brief}\n"
                "**Type** — Chartering or Sale & Purchase\n"
                "**Real Findings** — vessel/party details with source URLs\n"
                "**Match/Fit Assessment** — why this is a real, plausible opportunity\n"
                "**Next Step** — how TRoyMAR would approach it"
            ),
            agent=self.opportunity_finder,
        )
        crew = Crew(
            agents=[self.opportunity_finder],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Sales BROKERAGE for '{brief}':\n{result}",
            scope="/dept/sales/brokerage",
            categories=["sales", "brokerage"],
        )
        return result

    # ── SKILL: OUTREACH ────────────────────────────────────────────────────────────

    def outreach(self, prospect: str, channels: str = "email") -> str:
        task = Task(
            description=(
                f"{recall_context(prospect)}"
                f"OUTREACH: Write a personalized outreach sequence to: {prospect} via {channels}.\n\n"
                "Ground it in real, specific facts about their vessel/route/operations if known — "
                "never a generic template. Introduce TRoyMAR's real capability (ship agency, "
                "husbandry, chandlery/spares coordination, port logistics)."
            ),
            expected_output=(
                "## Outreach Sequence — {prospect}\n"
                "Multiple touchpoints (e.g. Day 1 intro, Day 4 follow-up, Day 8 close), each with "
                "subject/body, professional and grounded in real facts, no invented claims."
            ),
            agent=self.sales_head,
        )
        task_close = Task(
            description="Add one final, professional closing follow-up message for this sequence.",
            expected_output="One additional closing message.",
            agent=self.deal_closer,
            context=[task],
        )
        crew = Crew(
            agents=[self.sales_head, self.deal_closer],
            tasks=[task, task_close],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        crew_output = crew.kickoff()
        # Process.sequential only returns the LAST task's output from
        # kickoff() itself — pull every task's own output explicitly so the
        # main sequence isn't silently dropped (same real bug found and
        # fixed in TRoyAI's sales.py outreach()).
        result = (
            f"{str(crew_output.tasks_output[0])}\n\n---\n\n{str(crew_output.tasks_output[1])}"
            if len(crew_output.tasks_output) >= 2
            else str(crew_output)
        )
        remember(
            f"Sales OUTREACH for prospect '{prospect}' via {channels}:\n{result}",
            scope="/dept/sales/outreach",
            categories=["sales", "outreach"],
        )
        return result

    # ── SKILL: OBJECTION_HANDLER ──────────────────────────────────────────────────

    def objection_handler(self, objection: str) -> str:
        task = Task(
            description=(
                f"OBJECTION_HANDLER: Write an honest, credible response to this real objection: "
                f"{objection}"
            ),
            expected_output="A clear, honest, professional response — no overpromising to close a deal.",
            agent=self.sales_head,
        )
        crew = Crew(
            agents=[self.sales_head],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Sales OBJECTION_HANDLER for '{objection}':\n{result}",
            scope="/dept/sales/objection_handler",
            categories=["sales", "objection"],
        )
        return result

    # ── AGGREGATE ──────────────────────────────────────────────────────────────

    def run_pipeline(self, brief: str) -> str:
        task = Task(
            description=f"Plan the full sales pipeline for: {brief}. Cover opportunity finding, proposal, and closing steps.",
            expected_output="Sales pipeline plan with concrete next steps.",
            agent=self.sales_head,
        )
        crew = Crew(
            agents=[self.sales_head],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Sales pipeline for '{brief}':\n{result}",
            scope="/dept/sales/run_pipeline",
            categories=["sales", "pipeline"],
        )
        return result

    def find_opportunities(self, brief: str) -> str:
        """Research + report only — never drafts or sends outreach."""
        task = Task(
            description=(
                f"FIND_OPPORTUNITIES: Research real agency-appointment opportunities matching: "
                f"{brief}\n\nOnly include real, confirmed findings with sources. This is research "
                "and reporting only — do not draft any outreach."
            ),
            expected_output="Research report of real, sourced opportunities matching the brief.",
            agent=self.opportunity_finder,
        )
        crew = Crew(
            agents=[self.opportunity_finder],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Sales FIND_OPPORTUNITIES for '{brief}':\n{result}",
            scope="/dept/sales/find_opportunities",
            categories=["sales", "opportunities"],
        )
        return result
