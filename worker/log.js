// Temporary request log for the analysis of 4xx responses: every request goes through this Worker first
// (run_worker_first in wrangler.jsonc), is served from the static assets and written to the Workers Logs.
export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const url = new URL(request.url);
    console.log({
      method: request.method,
      path: url.pathname + url.search,
      status: response.status,
      userAgent: request.headers.get("user-agent"),
      ip: request.headers.get("cf-connecting-ip"),
      country: request.cf?.country,
    });
    return response;
  },
};
