# 28 — Global Headroom-only LLM Channel and Subscription Inheritance Spec

Status: active global policy  
Date: 2026-07-03  
Scope: Hermes, Nanobot, Graphify, Obsidian Operating Layer workers, and any local adapter that can call an external LLM

## Purpose

Make the LLM communication channels explicit, wide, and fail-closed so external LLM calls do not bypass Headroom, do not lose subscription/account inheritance, and do not get confused with local-only runtime dependencies such as Ollama.

This spec supersedes ad-hoc bridge guesses such as "point every OpenAI-compatible client at `/v1/responses`". A route is accepted only if the protocol shape, auth semantics, proxy path, and account-state handling are verified.

## Non-negotiable policy

All **external** LLM calls must go through Headroom.

Local exceptions are allowed only for local-only runtimes that do not call an external LLM provider, e.g. Ollama embeddings on `127.0.0.1:11434`.

Forbidden fallback behavior:

- direct `https://api.openai.com` or other provider traffic from adapters;
- raw API-key fallback just because Codex OAuth/Headroom is failing;
- silently switching to a heavier model, direct account, or external endpoint;
- marking a quota-limited account permanently dead;
- rotating accounts to hide a protocol mismatch or proxy outage.

## Authority and roles

| Layer | Role | Owns acceptance? | May change auth/proxy? |
|---|---|---:|---:|
| Hermes | Orchestrator, acceptance owner, safety verifier | yes | only with explicit user approval |
| Headroom | Local proxy/router/account-pool integration point | no | no |
| Codex CLI | Working external LLM transport through Headroom | no | no |
| Nanobot | Communication/report worker, connection scout, and proposal generator via bounded packets | no | no |
| Graphify | Graph/semantic adapter on sandbox/evidence inputs | no | no |
| Ollama | Local embedding runtime | no | no |

Hermes coordinates. Workers produce reports/proposals. No worker owns live apply or auth mutation.

## Canonical channel registry

### 1. Graphify external semantic extraction — accepted

```text
Graphify
  -> /home/hermesadmin/.local/bin/graphify-headroom
  -> GRAPHIFY_REQUIRE_HEADROOM=1
  -> backend=codex-cli
  -> Codex CLI profile, e.g. mini/impl/scout/review/max
  -> Headroom provider/config
  -> OAuth account/subscription pool
```

Accepted command shape:

```bash
graphify-headroom extract <sandbox-or-approved-corpus> --backend codex-cli
```

Required behavior:

- direct external OpenAI-compatible backend is blocked before network use unless its base URL is local Headroom;
- `codex-cli` route is allowed only when Codex config is Headroom-routed;
- Graphify does not own subscription/account selection; it inherits it from Codex CLI/Headroom;
- generated artifacts stay in sandbox/report output paths, not live vault mutation paths.

Current evidence:

- `graphify-headroom extract ... --backend codex-cli --no-viz` exited `0` and wrote `graph.json`;
- direct OpenAI with `GRAPHIFY_REQUIRE_HEADROOM=1` and non-local base URL exited `2` before network;
- Graphify backend tests passed: `77 passed`.

### 2. Ollama local embeddings — accepted local exception

```text
Embedding runner / local checks
  -> http://127.0.0.1:11434
  -> local model bge-m3
```

Ollama is not an external LLM proxy route. It is a localhost embedding dependency.

Required readiness gate before embedding work:

1. listener reachable at `127.0.0.1:11434`;
2. required model present, currently `bge-m3:latest`;
3. embedding endpoint returns expected dimensions;
4. runner is bounded by manifest, chunk size, max files, and stop-on-load policy.

If Ollama is unhealthy, degrade to report-only/graph-only. Do not replace it with an external embedding API unless explicitly approved and routed through Headroom.

### 3. Nanobot communication/review — accepted via Codex backend bridge wrapper

Nanobot is a communication/report worker. The accepted coordination pattern is:

```text
Hermes
  -> sanitized workspace-local packet under Nanobot workspace
  -> Nanobot reads packet
  -> Nanobot writes REPORT.md/proposal in the packet
  -> Hermes verifies and archives/accepts
```

The accepted external LLM launch is now the wrapper path:

```text
/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent
  -> Nanobot openai_codex HTTP provider
  -> NANOBOT_OPENAI_CODEX_RESPONSES_URL=http://127.0.0.1:8787/backend-api/codex/responses
  -> Headroom
  -> https://chatgpt.com/backend-api/codex/responses
  -> active Codex CLI OAuth account/subscription
```

Why the wrapper is required:

- generic `/v1/responses` is not the Nanobot default because it can bind to the wrong abstraction and stale cached auth;
- oauth-cli-kit's durable token cache can lag behind the active Codex CLI account, causing `401` even when Codex CLI through Headroom is healthy;
- the wrapper forces a per-run `OAUTH_CLI_KIT_TOKEN_PATH`, so oauth-cli-kit imports the active Codex CLI auth for that run without Hermes printing token material.

Current evidence:

- raw stale Nanobot cache produced HTTP `401` on Headroom-routed Codex backend;
- after per-run Codex CLI auth inheritance, Nanobot completed the report packet and Headroom logs showed `POST /backend-api/codex/responses` with `status=200` routed to `https://chatgpt.com/backend-api/codex/responses`;
- the completed Nanobot report lives at `/home/hermesadmin/.nanobot-hermes/workspace/communicator/inbox/headroom-global-spec-review-20260703T0600Z/REPORT.md`.

Do not run raw `nanobot agent` for external LLM work unless it has the same URL and per-run auth inheritance environment. Codex CLI `-p mini` through Headroom remains an accepted fallback independent reviewer for bounded, secret-free packets.

#### Nanobot as communicator and connection scout

Nanobot should be used as the broad communication/audit layer for connection architecture. For every old or new integration that may touch external LLMs, proxies, auth inheritance, provider SDKs, or subscription routing, Hermes can create a sanitized packet and ask Nanobot to return options before implementation.

Expected Nanobot output:

- available connection modes and protocol shapes;
- whether each mode can inherit Codex/Headroom subscription state;
- whether it can be made localhost-only / fail-closed;
- known blockers, stale-cache risks, quota behavior, and auth-repair paths;
- a recommended path plus fallback path;
- exact smoke checks Hermes should run.

Boundaries:

- Nanobot may search, compare, and propose;
- Nanobot may not read secrets or own auth mutation;
- Nanobot may not bypass Headroom for external LLM calls;
- Hermes verifies and applies.


Packet template for this role:

```text
/home/hermesadmin/.nanobot-hermes/templates/connection-scout-packet/
```

Use this template when evaluating any new SDK/provider/bridge or revisiting an old connection. The template forces the review to answer: protocol shape, Headroom compatibility, auth inheritance, fail-closed behavior, quota/auth failure classes, recommended route, fallback route, and Hermes smoke checks.

Minimum acceptance for the Nanobot wrapper path:

- no secrets printed in logs/reports;
- smoke request succeeds through Headroom;
- proxy logs/health prove traffic used Headroom;
- failure classes are separated: quota, auth invalidation, stale cache, proxy outage, protocol mismatch;
- report-only packet can be completed by Nanobot without direct external provider traffic.

## Subscription/account-state machine

Account/profile states must be explicit and reversible where appropriate.

| Observed failure | Class | Action | Re-entry |
|---|---|---|---|
| usage limit / quota exhausted | temporary capacity | cooldown, default ~5 hours | re-check after cooldown |
| rate limit burst | temporary capacity | shorter cooldown/backoff | re-check after backoff |
| `token_invalidated` / `refresh_token_invalidated` | auth failure | quarantine or switch to already configured account | only after login/repair or verified replacement |
| Headroom unhealthy / connection refused | proxy infra | stop and repair proxy | after health probe green |
| `/v1/responses` returns 401 for Codex OAuth headers | protocol mismatch | stop; fix bridge | after proper bridge implemented |
| model unsupported / config typo | config failure | stop; fix config | after config verification |

Never mark a usage-limited profile permanently dead. Never rotate accounts to mask bridge/protocol errors.

## Startup and smoke sequence

Before any full functional smoke:

1. Check Headroom:

```bash
curl -sS --max-time 5 http://127.0.0.1:8787/health
```

2. Check local Ollama if embeddings are in scope:

```bash
curl -sS --max-time 5 http://127.0.0.1:11434/api/tags
```

3. Check Graphify guard:

```bash
GRAPHIFY_REQUIRE_HEADROOM=1 OPENAI_BASE_URL=https://api.openai.com/v1 \
  /home/hermesadmin/tools/graphify/.venv/bin/python -m graphify extract <tiny-corpus> --backend openai --no-viz
```

Expected: fail-closed before external network.

4. Check Graphify working path:

```bash
graphify-headroom extract <tiny-corpus> --backend codex-cli --no-viz
```

Expected: success through Codex CLI/Headroom.

5. Nanobot Headroom bridge check:

```bash
/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent \
  <session-id> '<bounded report-only packet request>'
```

Expected: successful proposal-only response through Headroom. If this fails, do not silently fall back to a direct upstream provider.

## Nanobot consultation evidence

Hermes created a Nanobot communication packet:

```text
/home/hermesadmin/.nanobot-hermes/workspace/communicator/inbox/headroom-global-spec-review-20260703T0600Z/
```

The packet contains `ASK.md` and `evidence.json` asking Nanobot for report-only recommendations on this spec.

Actual Nanobot HTTP attempt through Headroom returned:

```text
Error calling Codex (CodexHTTPError): HTTP 401: Codex API request failed
```

This historical failure came from treating generic `/v1/responses` as the Nanobot/Codex route. The accepted path now uses the wrapper and Headroom backend Codex bridge; keep the old `/v1/responses` result only as a known anti-pattern.

A separate sanitized Codex CLI reviewer through Headroom agreed with the same recommendations: keep Graphify on `codex-cli -> Headroom`, fail-close direct external routes, implement a real Codex bridge for Nanobot, and split cooldown from auth invalidation.

## Implementation backlog

1. Keep and enforce `graphify-headroom` as the external Graphify entrypoint.
2. Keep `GRAPHIFY_REQUIRE_HEADROOM=1` in all Graphify external LLM task packets.
3. Add or finish Codex profile failover state machine:
   - usage-limit cooldown ~5h;
   - invalidated token quarantine;
   - proxy outage stop;
   - protocol mismatch stop.
4. Implement Nanobot bridge Option A or B above.
5. Done 2026-07-04: machine-readable channel registry and smoke schema exist: `docs/spec-kit/channel-registry.json`, `docs/spec-kit/schemas/llm-channel.schema.json`, and `make llm-channel-smoke`.
6. Done 2026-07-04: `make llm-channel-smoke-live` creates `out/reports/.../llm-channel-smoke.json` with local health probes and no secrets.
7. Keep older Nanobot/Graphify docs referencing this spec instead of the invalid `/v1/responses` assumption.

## Acceptance criteria

This problem is considered fixed only when all are true:

- Graphify external LLM smoke succeeds through Headroom.
- Direct external LLM smoke fails closed.
- Headroom health is verified before external LLM work.
- Ollama readiness is verified before local embedding work.
- Nanobot can complete a packet review through a valid Headroom/Codex bridge, not direct external traffic.
- Usage-limited accounts re-enter after cooldown and a fresh check.
- Invalidated auth is not treated as quota cooldown.
- The active route is documented in the packet/report for each worker run.
- Hermes remains acceptance owner and reports exact evidence paths.

## References

- Graphify wrapper: `/home/hermesadmin/.local/bin/graphify-headroom`
- Graphify runbook: `/home/hermesadmin/.config/graphify/HEADROOM_ONLY_RUNBOOK.md`
- Nanobot/Headroom runbook: `/home/hermesadmin/.nanobot-hermes/docs/HEADROOM_CHANNEL_RUNBOOK.md`
- Full-chain audit packet: `/home/hermesadmin/.nanobot-hermes/workspace/inbox/full-chain-proxy-login-ollama-graphify-audit-20260703T051328Z/REPORT.md`
- Nanobot consultation packet: `/home/hermesadmin/.nanobot-hermes/workspace/communicator/inbox/headroom-global-spec-review-20260703T0600Z/`
