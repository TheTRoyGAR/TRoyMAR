from crewai import Agent, Task, Crew, Process
from agency.core.llm import get_llm
from agency.core.memory import shared_memory, remember, recall_context
from agency.tools import search, scrape, write, read_file, list_dir


class ShippingDepartment:
    """Shipping & Ship Agency Operations Department — 1 head + 5 specialists. Skills: SUB_AGENT_NETWORK, PORT_CALL_LOGISTICS, HUSBANDRY_COORDINATION, TOOL_INTEGRATION, CARGO_LOGISTICS_MANAGEMENT."""

    def __init__(self):
        llm = get_llm("haiku")

        self.shipping_head = Agent(
            role="Head of Shipping & Ship Agency Operations",
            goal=(
                "As TRoyMAR's Hub Agent (General Agent) operation: identify and coordinate real "
                "local port agents as sub-agents at each port a client vessel calls, plan the "
                "real operational sequence for every call, arrange husbandry and chandlery needs, "
                "and keep TRoyMAR's own systems working correctly."
            ),
            backstory=(
                "You are the Head of Shipping & Ship Agency Operations at TRoy Maritime Agency (TRoyMAR). "
                "TRoyMAR operates as a Hub Agent (General Agent) — accountable to the shipowner/"
                "operator for the whole port-call relationship, while engaging real local port "
                "agents as sub-agents to do the physical, on-the-ground work at each specific "
                "port. Your goal is to identify and coordinate that sub-agent network, design the "
                "step-by-step logistics for a real port call — berth arrangement, customs "
                "clearance, crew/master needs — and coordinate husbandry and chandlery (spare "
                "parts, repairs) when a vessel needs them. You also own TRoyMAR's own technical "
                "systems.\n\n"
                "Your specific skills and responsibilities:\n"
                "1. SUB_AGENT_NETWORK — Identify real, reputable local port agents at a given port "
                "who could act as TRoyMAR's sub-agent there, and plan how TRoyMAR would oversee "
                "and coordinate that relationship on the shipowner's behalf. Never invent a real "
                "company name — if you can't confirm a real local agent, say so.\n"
                "2. PORT_CALL_LOGISTICS — Design the real step-by-step sequence for a port call: "
                "berth booking, pilotage, customs/immigration clearance, and husbandry needs.\n"
                "3. HUSBANDRY_COORDINATION — Plan how to source real spare parts and arrange "
                "repairs (main engine, plumbing, or other vessel needs) through real suppliers.\n"
                "4. TOOL_INTEGRATION — Determine which real tools/APIs TRoyMAR's own systems need "
                "(e.g. a public ship-tracking link, port authority notices, customs systems).\n"
                "5. CARGO_LOGISTICS_MANAGEMENT — Oversee the broader supply chain around a "
                "shipment: shippers, forwarders, carriers, multi-leg routing, and customs — the "
                "part of maritime logistics beyond the single port call.\n\n"
                "Never guess a real operational detail — a wrong berth time or missed customs step "
                "is a real, costly problem for a real ship.\n\n"
                "Operating rules: every operational recommendation must be grounded in real, "
                "current regulation or port procedure — if unverified, say so and flag what to "
                "check with a real port authority contact. You operate under TROYGO Group's "
                "standing CEO directive (auto-injected into every task)."
            ),
            llm=llm,
            tools=[write],
            verbose=False,
        )

        self.logistics_coordinator = Agent(
            role="Port Call Logistics Coordinator",
            goal="Plan the real step-by-step operational sequence for a vessel's port call.",
            backstory=(
                "You are the Port Call Logistics Coordinator at TRoy Maritime Agency. You design "
                "real berth, pilotage, and clearance sequences for vessel calls — grounded in real "
                "port procedures, not invented steps."
            ),
            llm=llm,
            tools=[search],
            verbose=False,
        )

        self.customs_compliance_specialist = Agent(
            role="Customs & Compliance Specialist",
            goal="Ensure every port call plan meets real customs, immigration, and port authority requirements.",
            backstory=(
                "You are the Customs & Compliance Specialist at TRoy Maritime Agency. You verify "
                "that a port call plan meets real regulatory requirements — never assume a "
                "shortcut exists."
            ),
            llm=llm,
            tools=[search, scrape],
            verbose=False,
        )

        self.husbandry_specialist = Agent(
            role="Vessel Husbandry Specialist",
            goal="Coordinate real crew/master needs and spare parts or repair sourcing for a vessel.",
            backstory=(
                "You are the Vessel Husbandry Specialist at TRoy Maritime Agency. You coordinate "
                "real husbandry needs — crew changes, provisions, medical, and sourcing real spare "
                "parts or repair services when something breaks (engine, plumbing, or other "
                "systems) — always through real, checkable suppliers."
            ),
            llm=llm,
            tools=[search],
            verbose=False,
        )

        self.cargo_logistics_manager = Agent(
            role="Cargo & Logistics Manager",
            goal=(
                "Manage the broader maritime supply chain around a shipment — connecting "
                "shippers, freight forwarders, and carriers, coordinating multi-leg cargo "
                "movement, and tracking real customs/compliance requirements — the part of "
                "maritime logistics that goes beyond a single vessel's single port call."
            ),
            backstory=(
                "You are the Cargo & Logistics Manager at TRoy Maritime Agency (TRoyMAR). Real "
                "maritime logistics is the planning, implementation, and control of goods moving "
                "by sea — cargo handling, freight forwarding, supply chain coordination, customs "
                "clearance, and risk management across the full movement of cargo, not just the "
                "port call of the ship carrying it. Roughly 80% of world trade by volume moves by "
                "sea, and the businesses that succeed in this industry are the ones that can "
                "actually manage that whole chain, not just service one ship in one port.\n\n"
                "Your specific skill:\n"
                "CARGO_LOGISTICS_MANAGEMENT — For a given cargo movement brief, identify the real "
                "shippers/forwarders/carriers involved or that would need to be, map the real "
                "multi-leg route the cargo has to take, flag the real customs/compliance "
                "checkpoints along the way, and note realistic freight-rate considerations. Never "
                "invent a specific real company, rate, or regulation you haven't actually "
                "confirmed — if something can't be verified, say so explicitly rather than "
                "guessing."
            ),
            llm=llm,
            tools=[search, scrape],
            verbose=False,
        )

        self.systems_integrator = Agent(
            role="Systems Integrator",
            goal="Integrate real external tools (ship tracking, port data) into TRoyMAR's own systems.",
            backstory=(
                "You are the Systems Integrator at TRoy Maritime Agency. You determine which real "
                "APIs/tools TRoyMAR's website and internal systems need, and write clean, working "
                "integration code."
            ),
            llm=llm,
            tools=[read_file, list_dir, write],
            verbose=False,
        )

    # ── SKILL: SUB_AGENT_NETWORK ──────────────────────────────────────────────────

    def sub_agent_network(self, target_port: str) -> str:
        task = Task(
            description=(
                f"{recall_context(target_port)}"
                f"SUB_AGENT_NETWORK: Identify real, reputable local port agents at: {target_port} "
                "who TRoyMAR could appoint as a sub-agent for handling on-the-ground port "
                "formalities (harbor master liaison, customs, immigration/police, berth) on "
                "TRoyMAR's behalf as Hub Agent.\n\n"
                "Only name a real, checkable company — search for and confirm it operates at this "
                "port. If you cannot confirm a real local agent, say so explicitly rather than "
                "inventing one."
            ),
            expected_output=(
                "## Sub-Agent Network — {target_port}\n"
                "**Candidate Local Agents** — real company name, what's confirmed about them, source URL\n"
                "**Coordination Plan** — how TRoyMAR as Hub Agent would oversee this sub-agent "
                "relationship (reporting, invoicing/DA flow-through, quality control)\n"
                "**Confidence Note** — explicitly state if no real candidate could be confirmed"
            ),
            agent=self.logistics_coordinator,
        )
        crew = Crew(
            agents=[self.logistics_coordinator],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Operations SUB_AGENT_NETWORK for '{target_port}':\n{result}",
            scope="/dept/operations/sub_agent_network",
            categories=["shipping", "sub_agent_network"],
        )
        return result

    # ── SKILL: PORT_CALL_LOGISTICS ────────────────────────────────────────────────

    def port_call_logistics(self, brief: str) -> str:
        task = Task(
            description=(
                f"{recall_context(brief)}"
                f"PORT_CALL_LOGISTICS: Design the real step-by-step operational plan for: {brief}\n\n"
                "Cover berth arrangement, pilotage, customs/immigration clearance, and any real "
                "husbandry needs. Ground it in real port procedures where known."
            ),
            expected_output=(
                "## Port Call Logistics Plan\n"
                "**Sequence** — numbered steps, berth through clearance\n"
                "**Key Contacts/Authorities** — who's involved at each step\n"
                "**Risks/Dependencies** — anything that could delay the call"
            ),
            agent=self.logistics_coordinator,
        )
        task_compliance = Task(
            description="Review the plan above for real customs/compliance gaps and correct them.",
            expected_output="The same plan, with compliance gaps flagged and corrected.",
            agent=self.customs_compliance_specialist,
            context=[task],
        )
        crew = Crew(
            agents=[self.logistics_coordinator, self.customs_compliance_specialist],
            tasks=[task, task_compliance],
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
            f"Operations PORT_CALL_LOGISTICS for '{brief}':\n{result}",
            scope="/dept/operations/port_call_logistics",
            categories=["shipping", "port_call"],
        )
        return result

    # ── SKILL: HUSBANDRY_COORDINATION ─────────────────────────────────────────────

    def husbandry_coordination(self, brief: str) -> str:
        task = Task(
            description=(
                f"{recall_context(brief)}"
                f"HUSBANDRY_COORDINATION: Plan real husbandry/spares/repair coordination for: "
                f"{brief}\n\nIdentify what's actually needed and how to source it through real "
                "suppliers or repair services — never invent a supplier or part."
            ),
            expected_output=(
                "## Husbandry Coordination Plan\n"
                "**Need** — what's actually required\n"
                "**Sourcing Plan** — real supplier/repair options if known, otherwise clearly "
                "marked as 'to be sourced locally'\n"
                "**Timeline** — realistic expectation"
            ),
            agent=self.husbandry_specialist,
        )
        crew = Crew(
            agents=[self.husbandry_specialist],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Operations HUSBANDRY_COORDINATION for '{brief}':\n{result}",
            scope="/dept/operations/husbandry_coordination",
            categories=["shipping", "husbandry"],
        )
        return result

    # ── SKILL: TOOL_INTEGRATION ───────────────────────────────────────────────────

    def tool_integration(self, integration_brief: str) -> str:
        task = Task(
            description=(
                f"{recall_context(integration_brief)}"
                f"TOOL_INTEGRATION: Determine what's needed to integrate: {integration_brief}\n\n"
                "Identify real APIs/tools required and how they'd connect into TRoyMAR's systems."
            ),
            expected_output=(
                "## Tool Integration Plan\n"
                "**What's Needed** — real tools/APIs\n"
                "**Integration Steps**\n"
                "**Notes/Constraints**"
            ),
            agent=self.systems_integrator,
        )
        crew = Crew(
            agents=[self.systems_integrator],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Operations TOOL_INTEGRATION for '{integration_brief}':\n{result}",
            scope="/dept/operations/tool_integration",
            categories=["shipping", "tool_integration"],
        )
        return result

    # ── SKILL: CARGO_LOGISTICS_MANAGEMENT ─────────────────────────────────────────

    def cargo_logistics_management(self, brief: str) -> str:
        task = Task(
            description=(
                f"{recall_context(brief)}"
                f"CARGO_LOGISTICS_MANAGEMENT: Plan the real broader supply-chain management for: "
                f"{brief}\n\n"
                "Identify the real shippers/forwarders/carriers involved or that would need to be "
                "engaged, map the real multi-leg route the cargo has to travel (not just the one "
                "port call), flag the real customs/compliance checkpoints along that route, and "
                "note realistic freight-rate considerations. If a specific company, rate, or "
                "regulation can't be verified, say so explicitly rather than inventing one."
            ),
            expected_output=(
                "## Cargo & Logistics Management Plan\n"
                "**Parties Involved** — real shippers/forwarders/carriers, confirmed or flagged as unconfirmed\n"
                "**Route** — the full multi-leg movement, not just one port call\n"
                "**Customs/Compliance Checkpoints** — where along the route\n"
                "**Freight-Rate Considerations** — realistic factors, not invented numbers\n"
                "**Confidence Note** — explicitly state anything that couldn't be verified"
            ),
            agent=self.cargo_logistics_manager,
        )
        crew = Crew(
            agents=[self.cargo_logistics_manager],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Operations CARGO_LOGISTICS_MANAGEMENT for '{brief}':\n{result}",
            scope="/dept/operations/cargo_logistics_management",
            categories=["shipping", "cargo_logistics"],
        )
        return result

    # ── AGGREGATE ──────────────────────────────────────────────────────────────

    def run_task(self, brief: str) -> str:
        task = Task(
            description=f"Plan the full operational approach for: {brief}.",
            expected_output="Operational plan covering logistics, husbandry, and any tooling needed.",
            agent=self.shipping_head,
        )
        crew = Crew(
            agents=[self.shipping_head],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Operations run_task for '{brief}':\n{result}",
            scope="/dept/operations/run_task",
            categories=["shipping", "task"],
        )
        return result

    def daily_briefing(self, context: str = "") -> str:
        task = Task(
            description=f"Produce a daily operations briefing. Context: {context or 'no specific context provided'}.",
            expected_output="Daily briefing: active port calls, pending husbandry needs, any operational risks.",
            agent=self.shipping_head,
        )
        crew = Crew(
            agents=[self.shipping_head],
            tasks=[task],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        result = str(crew.kickoff())
        remember(
            f"Operations daily briefing:\n{result}",
            scope="/dept/operations/daily_briefing",
            categories=["shipping", "briefing"],
        )
        return result
