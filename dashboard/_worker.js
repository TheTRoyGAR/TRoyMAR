// Locks dashboard.troymaritime.com behind HTTP Basic Auth at the edge, before
// any static file (including app.js, which carries the AGENT_API_KEY) is
// served. troymaritime.com/site is a separate Pages project and stays fully
// public — this only applies here.
export default {
  async fetch(request, env) {
    const auth = request.headers.get("Authorization");

    if (auth) {
      const [scheme, encoded] = auth.split(" ");
      if (scheme === "Basic" && encoded) {
        let decoded = "";
        try {
          decoded = atob(encoded);
        } catch {
          // fall through to 401
        }
        const idx = decoded.indexOf(":");
        const user = idx === -1 ? decoded : decoded.slice(0, idx);
        const pass = idx === -1 ? "" : decoded.slice(idx + 1);
        if (user === env.DASHBOARD_USER && pass === env.DASHBOARD_PASS) {
          return env.ASSETS.fetch(request);
        }
      }
    }

    return new Response("Authentication required", {
      status: 401,
      headers: { "WWW-Authenticate": 'Basic realm="TRoyMAR Command Centre"' },
    });
  },
};
