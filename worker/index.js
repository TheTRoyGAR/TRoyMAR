export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
      "Content-Type": "application/json",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    // The backend calls this route on its own (not the dashboard), once a
    // task finishes — authenticated with the shared secret it already
    // receives requests with (X-Backend-Key), not the dashboard's bearer token.
    const isCallbackRoute = /^\/api\/tasks\/[^/]+\/callback$/.test(path) && request.method === "POST";

    if (isCallbackRoute) {
      if (request.headers.get("X-Backend-Key") !== env.BACKEND_API_KEY) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401, headers: cors });
      }
    } else if (path !== "/api/health") {
      const authHeader = request.headers.get("Authorization");
      const apiKey = authHeader?.replace("Bearer ", "");
      if (apiKey !== env.AGENT_API_KEY) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401, headers: cors });
      }
    }

    try {
      if (path === "/api/health") {
        return json({ ok: true, agency: env.AGENCY_NAME, status: "online" }, cors);
      }

      if (path === "/api/departments" && request.method === "GET") {
        const { results } = await env.DB.prepare("SELECT * FROM departments ORDER BY name").all();
        return json({ departments: results }, cors);
      }

      if (path === "/api/agents" && request.method === "GET") {
        const dept = url.searchParams.get("department");
        const stmt = dept
          ? env.DB.prepare("SELECT * FROM agents WHERE department = ? ORDER BY name").bind(dept)
          : env.DB.prepare("SELECT * FROM agents ORDER BY department, name");
        const { results } = await stmt.all();
        return json({ agents: results }, cors);
      }

      if (path === "/api/tasks" && request.method === "GET") {
        const { results } = await env.DB.prepare("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50").all();
        return json({ tasks: results }, cors);
      }

      if (path === "/api/tasks" && request.method === "POST") {
        const body = await request.json();
        const { department, agent, task, input } = body;
        if (!department || !task) return json({ error: "department and task are required" }, cors, 400);

        const id = crypto.randomUUID();
        await env.DB.prepare(
          "INSERT INTO tasks (id, department, agent, task, input, status, created_at) VALUES (?, ?, ?, ?, ?, 'queued', datetime('now'))"
        ).bind(id, department, agent || "auto", task, input || "").run();

        if (env.BACKEND_URL) {
          ctx.waitUntil(executeTask(env, id, department, task, input || ""));
        }

        return json({ task_id: id, status: "queued" }, cors, 201);
      }

      if (path.startsWith("/api/tasks/") && request.method === "GET") {
        const taskId = path.split("/").pop();
        const result = await env.DB.prepare("SELECT * FROM tasks WHERE id = ?").bind(taskId).first();
        if (!result) return json({ error: "Task not found" }, cors, 404);
        return json(result, cors);
      }

      if (isCallbackRoute) {
        const taskId = path.split("/")[3];
        const body = await request.json();
        const status = body.status === "failed" ? "failed" : "completed";
        await env.DB.prepare(
          "UPDATE tasks SET status = ?, output = ?, completed_at = datetime('now') WHERE id = ?"
        ).bind(status, String(body.output || "").slice(0, 4000), taskId).run();
        return json({ received: true }, cors, 200);
      }

      if (path === "/api/memory" && request.method === "GET") {
        if (!env.BACKEND_URL) return json({ count: 0, records: [] }, cors);
        const backendRes = await fetch(`${env.BACKEND_URL}/memory/records`, {
          headers: { "X-Backend-Key": env.BACKEND_API_KEY || "" },
        });
        if (!backendRes.ok) {
          const errText = await backendRes.text();
          return json({ error: "Backend unavailable", detail: errText.slice(0, 500) }, cors, 502);
        }
        return json(await backendRes.json(), cors);
      }

      return json({ error: "Not found" }, cors, 404);
    } catch (err) {
      return json({ error: err.message }, cors, 500);
    }
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(sweepStaleTasks(env));
  },
};

function json(data, headers, status = 200) {
  return new Response(JSON.stringify(data), { status, headers });
}

// Kickoff only bounds the initial handshake (backend accepted the job) —
// the backend runs the real crew in the background and POSTs the result to
// /api/tasks/:id/callback whenever it finishes, however long that takes.
const ACCEPT_TIMEOUT_MS = 20 * 1000;

async function executeTask(env, id, department, task, input) {
  try {
    await env.DB.prepare("UPDATE tasks SET status = 'running' WHERE id = ?").bind(id).run();

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), ACCEPT_TIMEOUT_MS);
    let res;
    try {
      res = await fetch(`${env.BACKEND_URL}/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Backend-Key": env.BACKEND_API_KEY || "" },
        body: JSON.stringify({
          task_id: id,
          department,
          skill: task,
          brief: input,
          callback_url: `${env.WORKER_PUBLIC_URL}/api/tasks/${id}/callback`,
        }),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeout);
    }

    if (!res.ok) {
      const errText = await res.text();
      await env.DB.prepare(
        "UPDATE tasks SET status = 'failed', output = ?, completed_at = datetime('now') WHERE id = ?"
      ).bind(errText.slice(0, 4000), id).run();
    }
    // On success the task stays 'running' — the callback above marks it
    // completed/failed once the backend actually finishes.
  } catch (err) {
    await env.DB.prepare(
      "UPDATE tasks SET status = 'failed', output = ?, completed_at = datetime('now') WHERE id = ?"
    ).bind(String(err.message || err).slice(0, 4000), id).run();
  }
}

// Backstop for a backend crash/restart after accepting a job but before
// calling back — without this the task would sit at 'running' forever.
const STALE_TASK_MINUTES = 20;

async function sweepStaleTasks(env) {
  await env.DB.prepare(
    `UPDATE tasks SET status = 'failed',
       output = 'Timed out - no result received from the backend within ${STALE_TASK_MINUTES} minutes. It may have crashed or restarted mid-task.',
       completed_at = datetime('now')
     WHERE status = 'running' AND created_at < datetime('now', '-${STALE_TASK_MINUTES} minutes')`
  ).run();
}
