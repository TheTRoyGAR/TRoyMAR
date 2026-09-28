from crewai import Agent, Task, Crew, Process
from agency.core.llm import get_llm
from agency.core.memory import shared_memory, remember, recall_context
from agency.tools import search, write, read_file, list_dir


class CTODepartment:
    """CTO Department — 5 agents running all technology for TRoyMAR.

    Real audit capability (added 2026-09-27): before this, none of these
    agents had any tool at all — no way to read the real codebase, so any
    "audit" or "fix" they produced was invented from training memory, not
    grounded in TRoyMAR's actual code. Modeled on TRoyGO's CTO department
    (TRoyLAB-Repo/agency/departments/cto.py), which already had this
    fixed: read-only-first (code_reviewer/security_auditor can only read,
    never write), audit_codebase() is the real entry point for "find real
    bugs," and run_task/security_audit/deploy are kept as-is for the
    existing server.py routes.
    """

    def __init__(self):
        llm_opus = get_llm("opus")
        llm = get_llm("sonnet")

        self.developer = Agent(
            role="Software Developer",
            goal="Write, maintain, and improve all code for TRoyMAR's products and infrastructure",
            backstory=(
                "You are the Software Developer at TRoy Maritime Agency (TRoyMAR). "
                "You build Python agents, Cloudflare Pages sites, and web dashboards. "
                "Stack: Python, CrewAI, Cloudflare Pages, D1."
            ),
            llm=llm_opus,
            tools=[search, write],
            verbose=False,
        )

        self.code_reviewer = Agent(
            role="Code Reviewer",
            goal="Find real bugs in TRoyMAR's codebase — dead links, unwired features, silent failures, truncation/config bugs.",
            backstory=(
                "You are the Code Reviewer at TRoy Maritime Agency (TRoyMAR). You review the "
                "real code for bugs and maintainability issues. You are READ-ONLY — you have no "
                "write tool and must never claim to have fixed anything, only report what you "
                "actually find in the real files you read."
            ),
            llm=llm,
            tools=[read_file, list_dir],
            max_iter=40,
            verbose=False,
        )

        self.architect = Agent(
            role="System Architect",
            goal="Design scalable, reliable system architecture for all TRoyMAR products",
            backstory=(
                "You are the System Architect at TRoy Maritime Agency (TRoyMAR). "
                "You make high-level technology decisions, design data models, "
                "and ensure the system can scale as TRoyMAR grows."
            ),
            llm=llm_opus,
            tools=[search],
            verbose=False,
        )

        self.security_auditor = Agent(
            role="Security Auditor",
            goal="Identify real security vulnerabilities across all TRoyMAR systems",
            backstory=(
                "You are the Security Auditor at TRoy Maritime Agency (TRoyMAR). You check for "
                "OWASP Top 10 issues, exposed keys, and unsafe patterns in the real code. You "
                "never reproduce the actual contents of secret/credential files (.env, keys, "
                "tokens) — only note that one exists and where, never its value."
            ),
            llm=llm,
            tools=[read_file, list_dir],
            max_iter=40,
            verbose=False,
        )

        self.devops = Agent(
            role="DevOps Engineer",
            goal="Deploy, monitor, and maintain all TRoyMAR infrastructure on Cloudflare",
            backstory=(
                "You are the DevOps Engineer at TRoy Maritime Agency (TRoyMAR). "
                "You manage deployments to Cloudflare Pages and D1. "
                "You ensure 99.9% uptime and fast deployments."
            ),
            llm=llm,
            verbose=False,
        )

    # ── SKILL: AUDIT_CODEBASE (real, read-only scan & report) ──────────────────

    def audit_codebase(self, target_dir: str = ".") -> str:
        target_dir = target_dir.strip() or "."
        task_scan = Task(
            description=(
                f"{recall_context(target_dir)}"
                f"AUDIT_CODEBASE: Read and review the real code under '{target_dir}' (relative "
                "to the TRoyMAR repo root — covers server.py, the agency/ CrewAI backend, and "
                "the site/ Cloudflare Pages site). List the directory structure first, then open "
                "and read the files that matter most. Look for real bugs: features that look "
                "built but aren't wired up, dead links, dead code, broken logic, silently "
                "unhandled cases, config values (like max_tokens caps) that don't match what a "
                "real task actually needs, and inconsistencies between related files.\n\n"
                "Hard rules: you are READ-ONLY. Do not attempt to write, edit, or modify any "
                "file — you have no write tool and must not ask for one. If you encounter a "
                ".env, credentials, or key/token file, note only that it exists and its path — "
                "never quote or reproduce its contents.\n\n"
                "Scope discipline (this is what previously blew the context budget elsewhere in "
                "this codebase): never read node_modules, .next, out, dist, .venv, __pycache__, "
                "or any other generated/dependency directory — skip them entirely, do not even "
                "list their contents. Read at most 20 files total, prioritizing real application "
                "source over config/lockfiles. Never read the same file twice — track what "
                "you've already opened. If the tree is large, sample the most important-looking "
                "files rather than trying to cover everything; a partial, honest audit beats one "
                "that fails outright."
            ),
            expected_output=(
                "## Codebase Audit — <target_dir>\n"
                "For each real finding: **File** (path) · **Issue** (what's wrong) · "
                "**Suggested Fix** (described in words, not applied) · **Severity** "
                "(HIGH/MEDIUM/LOW). If nothing meaningful is found, say so plainly — "
                "do not invent issues to pad the report."
            ),
            agent=self.code_reviewer,
        )
        task_security = Task(
            description=(
                "Review the same area specifically for security issues: hardcoded secrets, "
                "injection risks, missing auth checks, exposed internal endpoints. Same "
                "read-only rules apply — never reproduce secret values, only flag their "
                "presence and location."
            ),
            expected_output="## Security Findings\nPASS, or a list of: **File** · **Risk** · **Fix** · **Severity**.",
            agent=self.security_auditor,
            context=[task_scan],
        )
        crew = Crew(
            agents=[self.code_reviewer, self.security_auditor],
            tasks=[task_scan, task_security],
            process=Process.sequential,
            memory=shared_memory,
            verbose=False,
        )
        crew_output = crew.kickoff()
        result = (
            f"## Codebase Audit — {target_dir}\n\n{crew_output.tasks_output[0].raw}\n\n"
            f"---\n\n{crew_output.tasks_output[1].raw}"
        )
        remember(
            f"CTO AUDIT_CODEBASE for '{target_dir}':\n{result}",
            scope="/dept/cto/audit_codebase",
            categories=["cto", "audit"],
            importance=0.6,
        )
        return result

    # ── Existing skills, kept as-is for the existing server.py routes ─────────

    def run_task(self, brief: str) -> str:
        task_arch = Task(
            description=f"Design the technical approach for: {brief}",
            expected_output="Technical design: components, data flow, stack choices. Max 200 words.",
            agent=self.architect,
        )

        task_dev = Task(
            description="Implement the solution based on the architect's design.",
            expected_output="Complete working code with inline comments on non-obvious parts only.",
            agent=self.developer,
            context=[task_arch],
        )

        task_review = Task(
            description="Review the code for bugs, security issues, and quality.",
            expected_output="Review summary: APPROVED or NEEDS CHANGES, with specific issues listed.",
            agent=self.code_reviewer,
            context=[task_dev],
        )

        crew = Crew(
            agents=[self.architect, self.developer, self.code_reviewer],
            tasks=[task_arch, task_dev, task_review],
            process=Process.sequential,
            verbose=False,
        )

        return str(crew.kickoff())

    def security_audit(self, target: str) -> str:
        task = Task(
            description=f"Run a security audit on: {target}. Check OWASP top 10.",
            expected_output="Security report: CRITICAL, HIGH, MEDIUM, LOW findings with remediation steps.",
            agent=self.security_auditor,
        )

        crew = Crew(agents=[self.security_auditor], tasks=[task], process=Process.sequential, verbose=False)
        return str(crew.kickoff())

    def deploy(self, what: str) -> str:
        task = Task(
            description=f"Create deployment plan and commands for: {what}. Target: Cloudflare.",
            expected_output="Step-by-step deployment commands with verification steps.",
            agent=self.devops,
        )

        crew = Crew(agents=[self.devops], tasks=[task], process=Process.sequential, verbose=False)
        return str(crew.kickoff())
