const JSON_HEADERS = { "content-type": "application/json; charset=utf-8" };

function parseAllowedOrigins(value) {
  return (value || "")
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);
}

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = parseAllowedOrigins(env.ALLOWED_ORIGINS);
  const headers = {
    "access-control-allow-methods": "GET, OPTIONS",
    "access-control-allow-headers": "content-type",
    "access-control-max-age": "86400",
  };

  if (allowed.includes("*")) {
    headers["access-control-allow-origin"] = "*";
  } else if (origin && allowed.includes(origin)) {
    headers["access-control-allow-origin"] = origin;
    headers["vary"] = "Origin";
  }

  return headers;
}

function jsonResponse(request, env, body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      ...JSON_HEADERS,
      ...corsHeaders(request, env),
    },
  });
}

function errorResponse(request, env, status, message) {
  return jsonResponse(request, env, { error: message }, status);
}

async function readJson(kv, key) {
  const raw = await kv.get(key);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function pickRandomId(ids) {
  if (!Array.isArray(ids) || ids.length === 0) return null;
  return ids[Math.floor(Math.random() * ids.length)];
}

async function handleMeta(request, env) {
  const meta = await readJson(env.QUESTIONS, "meta");
  if (!meta) {
    return errorResponse(request, env, 503, "题库尚未同步，请稍后再试。");
  }
  return jsonResponse(request, env, meta);
}

async function handleRandom(request, env) {
  const url = new URL(request.url);
  const subject = (url.searchParams.get("subject") || "").trim();
  const difficulty = (url.searchParams.get("difficulty") || "all").trim() || "all";

  if (!subject) {
    return errorResponse(request, env, 400, "请提供 subject 参数。");
  }

  const indexKey = `idx:${subject}:${difficulty}`;
  let ids = await readJson(env.QUESTIONS, indexKey);

  if (!ids && difficulty !== "all") {
    ids = await readJson(env.QUESTIONS, `idx:${subject}:all`);
  }

  const questionId = pickRandomId(ids);
  if (!questionId) {
    return errorResponse(request, env, 404, "当前筛选条件下没有可用题目。");
  }

  const question = await readJson(env.QUESTIONS, `q:${questionId}`);
  if (!question) {
    return errorResponse(request, env, 404, "题目不存在或尚未同步。");
  }

  return jsonResponse(request, env, question);
}

async function handleSolution(request, env) {
  const url = new URL(request.url);
  const questionId = (url.searchParams.get("id") || "").trim();
  if (!questionId) {
    return errorResponse(request, env, 400, "请提供 id 参数。");
  }

  const solution = await readJson(env.QUESTIONS, `sol:${questionId}`);
  if (!solution) {
    return errorResponse(request, env, 404, "暂无解析。");
  }

  return jsonResponse(request, env, solution);
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(request, env),
      });
    }

    if (request.method !== "GET") {
      return errorResponse(request, env, 405, "仅支持 GET 请求。");
    }

    const { pathname } = new URL(request.url);

    if (pathname === "/api/meta") {
      return handleMeta(request, env);
    }

    if (pathname === "/api/random") {
      return handleRandom(request, env);
    }

    if (pathname === "/api/solution") {
      return handleSolution(request, env);
    }

    if (pathname === "/" || pathname === "/health") {
      return jsonResponse(request, env, { ok: true, service: "yudongyi-practice-api" });
    }

    return errorResponse(request, env, 404, "未找到接口。");
  },
};
