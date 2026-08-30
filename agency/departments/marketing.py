from crewai import Agent, Task, Crew, Process
from agency.core.llm import get_llm
from agency.core.memory import shared_memory, remember, recall_context
from agency.tools import search, scrape, write


class MarketingDepartment:
    """Marketing Department — 1 head + 4 specialists. Skills: PORT_CALL_INTEL, CAPABILITY_CONTENT, REPUTATION_AUDIT."""

    def __init__(self):
        llm = get_llm("haiku")

        self.marketing_head = Agent(
            role="Head of the AI Marketing Department",
            goal=(
                "Build TRoy Maritime Agency's reputation and visibility with ship owners, "
                "operators, and charterers by tracking real port-call activity and producing "
                "credible, industry-accurate content — never generic corporate copy."
            ),
            backstory=(
                "You are the Head of the AI Marketing Department at TRoy Maritime Agency "
                "(TRoyMAR). Your goal is to make TRoyMAR visible and credible to the people who "
                "actually decide which agent handles a port call — operations managers, port "
                "captains, and DPAs at shipping companies.\n\n"
                "You possess three core skills:\n"
                "1. PORT_CALL_INTEL — Research real, currently-scheduled vessel calls at target "
                "ports (cruise and cargo) to identify which lines/operators are worth approaching, "
                "and when. Never invent a vessel call — confirm it on a real source.\n"
                "2. CAPABILITY_CONTENT — Write clear, accurate capability statements, port service "
                "briefs, and website copy that describe what TRoyMAR actually does (ship agency, "
                "husbandry, chandlery/spares coordination, port logistics) — no invented "
                "credentials or client claims.\n"
                "3. REPUTATION_AUDIT — Review TRoyMAR's own public presence (website, listings) "
                "and flag anything inaccurate, outdated, or unclear to a prospective client.\n\n"
                "All content must be industry-accurate and verifiable. In this business, an "
                "exaggerated claim gets caught immediately by people who actually know the port.\n\n"
                "Operating rules: all port intelligence content must cite a real, checkable source "
                "(a real news article, a real port authority notice) — never a plausible-sounding "
                "but unverified fact. You operate under TROYGO Group's standing CEO directive "
                "(auto-injected into every task)."
            ),
            llm=llm,
            tools=[write],
            verbose=False,
        )

        self.port_intel_analyst = Agent(
            role="Port Intelligence Analyst",
            goal="Research real, currently-scheduled vessel calls and industry activity at target ports.",
            backstory=(
                "You are the Port Intelligence Analyst at TRoy Maritime Agency. You track real "
                "vessel schedules, port authority notices, and shipping line activity — always "
                "from real, checkable sources, never assumed or estimated."
            ),
            llm=llm,
            tools=[search, scrape],
            verbose=False,
        )

        self.content_creator = Agent(
            role="Content Creator",
            goal="Write accurate, professional capability statements and industry content for TRoyMAR.",
            backstory=(
                "You are the Content Creator at TRoy Maritime Agency. You write clear, "
                "professional copy describing TRoyMAR's real services — ship agency, husbandry, "
                "chandlery, and port logistics — without embellishment."
            ),
            llm=llm,
            tools=[write],
            verbose=False,
        )

        self.industry_relations_manager = Agent(
            role="Industry Relations Manager",
            goal="Identify and map the right shipping lines, operators, and port authorities to build relationships with.",
            backstory=(
                "You are the Industry Relations Manager at TRoy Maritime Agency. You track which "
                "cruise and cargo lines, port authorities, and industry bodies (like CLIA, AMSA) "
                "matter most to TRoyMAR's growth, and how to approach them credibly."
            ),
            llm=llm,
            verbose=False,
        )

        self.reputation_reporter = Agent(
            role="Reputation & Analytics Reporter",
            goal="Track TRoyMAR's public presence and real engagement, and report on it honestly.",
            backstory=(
                "You are the Reputation & Analytics Reporter at TRoy Maritime Agency. You monitor "
                "how TRoyMAR is presented publicly and report real findings — never invented "
                "metrics."
            ),
            llm=llm,
            verbose=False,
        )

    # ── SKILL: PORT_CALL_INTEL ──────────────────────────────────────────────────

    def port_call_intel(self, target_port: str) -> str:
        task = Task(
            description=(
                f"{recall_context(target_port)}"
                f"PORT_CALL_INTEL: Research real, currently-scheduled vessel calls at: {target_port}\n\n"
                "Search for real port schedules, port authority notices, and cruise/cargo line "
                "announcements. For every vessel call listed, confirm it on a real source page "
                "before including it. Never invent a vessel name, date, or line."
            ),
            expected_output=(
                "## Port Call Intelligence — {target_port}\n"
                "**Confirmed Upcoming Calls** — vessel, line, date, source URL for each\n"
                "**Notable Operators** — which lines call most often\n"
                "**Opportunity Notes** — which calls are worth a direct approach and why"
            ),
            agent=self.port_intel_analyst,
        )
        crew = Crew(
            agents=[self.port_intel_analyst],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Marketing PORT_CALL_INTEL for '{target_port}':\n{result}",
            scope="/dept/marketing/port_call_intel",
            categories=["marketing", "port_intel"],
        )
        return result

    # ── SKILL: CAPABILITY_CONTENT ─────────────────────────────────────────────────

    def capability_content(self, brief: str) -> str:
        task = Task(
            description=(
                f"{recall_context(brief)}"
                f"CAPABILITY_CONTENT: Write accurate capability content for: {brief}\n\n"
                "Describe TRoyMAR's real services — ship agency, husbandry, chandlery/spares "
                "coordination, port logistics — clearly and professionally. No invented client "
                "names, no fabricated credentials or years of operation."
            ),
            expected_output=(
                "## Capability Content\n"
                "Ready-to-publish copy addressing the brief, professional tone, no fabricated claims."
            ),
            agent=self.marketing_head,
        )
        task_write = Task(
            description="Polish the draft into final, publish-ready copy with clear structure and headings.",
            expected_output="Final, publish-ready content.",
            agent=self.content_creator,
            context=[task],
        )
        crew = Crew(
            agents=[self.marketing_head, self.content_creator],
            tasks=[task, task_write],
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
            f"Marketing CAPABILITY_CONTENT for '{brief}':\n{result}",
            scope="/dept/marketing/capability_content",
            categories=["marketing", "content"],
        )
        return result

    # ── SKILL: REPUTATION_AUDIT ───────────────────────────────────────────────────

    def reputation_audit(self, target: str) -> str:
        task = Task(
            description=(
                f"{recall_context(target)}"
                f"REPUTATION_AUDIT: Review TRoyMAR's public presence for: {target}\n\n"
                "Flag anything inaccurate, outdated, unclear, or missing that a prospective "
                "client (ship owner/operator) would notice."
            ),
            expected_output=(
                "## Reputation Audit\n"
                "**Findings** — specific, real issues found\n"
                "**Recommendations** — concrete fixes, prioritized"
            ),
            agent=self.reputation_reporter,
        )
        crew = Crew(
            agents=[self.reputation_reporter],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Marketing REPUTATION_AUDIT for '{target}':\n{result}",
            scope="/dept/marketing/reputation_audit",
            categories=["marketing", "reputation"],
        )
        return result

    # ── AGGREGATE ──────────────────────────────────────────────────────────────

    def run_campaign(self, brief: str) -> str:
        task = Task(
            description=f"Plan a full marketing push for: {brief}. Cover port-call intelligence, content, and industry relationship targets.",
            expected_output="Marketing plan: intel targets, content pieces, and relationship targets.",
            agent=self.marketing_head,
        )
        crew = Crew(
            agents=[self.marketing_head],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Marketing campaign for '{brief}':\n{result}",
            scope="/dept/marketing/run_campaign",
            categories=["marketing", "campaign"],
        )
        return result
