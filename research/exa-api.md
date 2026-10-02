# Exa API build reference (checked live on 2026-09-29)

## 0. Read this first

**How I gathered this.** docs.exa.ai now sends a 307 redirect (a temporary "go here instead" response) to https://exa.ai/docs. I downloaded the docs' machine-readable index at https://docs.exa.ai/llms.txt (which lists every page under exa.ai/docs), about 45 of the Markdown pages, and the OpenAPI spec at https://exa.ai/docs/exa-spec.yaml. An OpenAPI spec is a machine-readable file that lists every endpoint and field. This one is titled "Exa Public API", version 2.0.0, and the docs call it "the source of truth for request and response schemas". I also read the current SDK source on GitHub (exa-py `exa_py/api.py`, `exa_py/agent/client.py`, `exa_py/research/*`, and exa-js `src/index.ts`) and checked package versions on PyPI and npm.

I made no authenticated API calls, because I have no key and did not create an account. An unauthenticated call to /search returns an x402 payment challenge (HTTP 402, tag `X402_PAYMENT_REQUIRED`, quoting $0.007) before any validation runs. So nothing below was tested against a live key.

**What exists today, in one line each:**
- **Search** (`POST /search`): six modes, from `instant` to `deep-reasoning`. It can return page contents and a synthesized, cited JSON answer in the same call.
- **Contents** (`POST /contents`): clean text, highlights or summaries for URLs you already have.
- **Answer** (`POST /answer`): an LLM answer with citations.
- **Exa Agent** (`/agent/runs`): asynchronous (runs in the background) research, list building and enrichment. It returns schema-validated JSON with citations for each field. Launched 2026-06-16.
- **Monitors** (`/monitors`): scheduled searches that post new results to a webhook.
- **Websets** (`/websets/v0/...`): verified, enriched entity lists. Separate paid plan. The docs now steer new work to Agent.
- **Batch** (`/batches`): Enterprise-only beta.
- **OpenAI-compatible endpoints:** `/chat/completions` (routes to Answer) and `/responses` (routes to Agent).
- **Team Management API:** create and manage API keys programmatically.
- **Hosted MCP server** at https://mcp.exa.ai/mcp.

**What is gone or deprecated:**
- The **Research API (`/research`) was retired on April 1, 2026** and replaced by `/search` with `type: "deep-reasoning"`.
- `/findSimilar` is deprecated.
- `livecrawl` is replaced by `maxAgeHours`.
- `includeText` / `excludeText` are deprecated.
- `startCrawlDate` / `endCrawlDate` are ignored.
- `useAutoprompt` is removed.
- `numSentences` / `highlightsPerUrl` are deprecated.
- Categories `research paper` (now `publication`), `linkedin` (now `people`), `pdf`, `github` and `tweet` are deprecated.

## 1. Basics

- **Base URL:** `https://api.exa.ai`. Websets paths sit under the base `https://api.exa.ai/websets` (for example `https://api.exa.ai/websets/v0/websets`).
- **Auth:** send either `x-api-key: $EXA_API_KEY` or `Authorization: Bearer $EXA_API_KEY`. Both SDKs send `x-api-key`.
- **Key:** create it at https://dashboard.exa.ai/api-keys. Both SDKs read the `EXA_API_KEY` environment variable. You can also pass it inline: `Exa(api_key="...")` in Python or `new Exa("...")` in JS.
- **Useful response headers:** `x-request-id` (quote it to support), `x-exa-queued` and `x-exa-queue-ms` (whether and how long the request waited in your rate-limit queue).
- **Error body:** `{requestId, error, tag}`. Branch on the HTTP status first. The docs say the list of tags is open-ended, so unknown tags must not break your code.
- **Status page:** https://status.exa.ai. Machine-readable versions are https://status.exa.ai/summary.json and https://status.exa.ai/v2/components.json.

## 2. Endpoint catalog

| Method + path | What it does | Sync or async | List price |
|---|---|---|---|
| POST /search | Web search, optional contents, optional synthesized output | Sync (SSE streaming only with outputSchema) | instant $4/1k; fast and auto $7/1k; deep-lite and deep $12/1k; deep-reasoning $15/1k (base covers 10 results) |
| POST /contents | Text, highlights or summary for known URLs | Sync | $1/1k pages per content type |
| POST /answer | LLM answer plus citations | Sync or SSE | $5/1k |
| POST /findSimilar | Pages similar to a URL (DEPRECATED) | Sync | not listed on the pricing page |
| POST /agent/runs, GET /agent/runs, GET/DELETE /agent/runs/{id}, POST /agent/runs/{id}/cancel, POST /agent/runs/{id}/stop, GET /agent/runs/{id}/events | Exa Agent | Async (poll, SSE, or replay stored events) | fixed effort $0.012 to $1.00 per run, or metered |
| POST/GET /monitors, POST /monitors/batch, GET/PATCH/DELETE /monitors/{id}, POST /monitors/{id}/trigger, GET /monitors/{id}/runs, GET /monitors/{id}/runs/{runId} | Scheduled searches that call a webhook | Async | $15/1k runs |
| POST/GET /batches, GET/DELETE /batches/{id}, POST /batches/{id}/cancel | Bulk async /search and /agent/runs (Enterprise beta) | Async, JSONL results | contract |
| /websets/v0/websets (+ /{id}, /{id}/cancel, /preview, /{webset}/searches, /enrichments, /items), /v0/imports, /v0/monitors, /v0/webhooks, /v0/events, GET /v0/teams/me | Websets | Async | Websets credits (separate plan) |
| POST /chat/completions (model `exa`) | OpenAI Chat Completions interface, routes to /answer | Sync or stream | as /answer |
| POST /responses, GET /responses/{id}, POST /responses/{id}/cancel (model `exa-agent`) | OpenAI Responses interface, routes to Agent | sync, stream or background | as Agent |
| https://admin-api.exa.ai/team-management/api-keys (+ /{id}, /{id}/usage) | Create, list, update and delete API keys, set per-key `rateLimit` and `budgetCents` | Sync | enabled per team on request |

### 2.1 POST /search

**Request fields** (exact spelling from the OpenAPI spec; SDK Python names are snake_case versions):

| Field | Type / limits | Notes |
|---|---|---|
| `query` | string, required, min length 1 | Write it in natural language and describe the pages you want. |
| `type` | `instant`, `fast`, `auto` (default), `deep-lite`, `deep`, `deep-reasoning` | See section 3. |
| `numResults` | integer 1 to 100, default 10 | No pagination. The base price covers 10; each extra result costs $1/1k. |
| `includeDomains` / `excludeDomains` | array, max 1200 entries | Each entry can be a hostname (`example.com`), a hostname plus path prefix (`example.com/docs`), or a subdomain wildcard (`*.substack.com`). Use these instead of `site:` in the query. |
| `startPublishedDate` / `endPublishedDate` | ISO 8601 date-time | Filters on publication date, which Exa estimates by parsing the page. |
| `category` | `company`, `publication`, `news`, `personal site`, `financial report`, `people` | Other strings are accepted as hints. `company` and `people` reject `startPublishedDate`, `endPublishedDate` and `excludeDomains` with a 400. |
| `userLocation` | two-letter ISO country code, e.g. `US` | Biases results toward that region. |
| `moderation` | boolean, default false | Filters unsafe content. |
| `contents` | object (see section 5) | Holds `text`, `highlights`, `summary`, `extras`, `maxAgeHours`, `livecrawlTimeout`, `snapshotAsOf`, `subpages`, `subpageTarget`. |
| `additionalQueries` | array of 1 to 10 strings | Deep types only. Extra search angles that run alongside the main query. |
| `systemPrompt` | string | Guidance on source preferences, novelty and dedupe (removing duplicates), for synthesis and deep research. |
| `outputSchema` | `{type:"text", description}` or `{type:"object", properties, required, ...}` | Triggers synthesis and adds about 2 s. Object schemas allow at most 10 properties in total (nested and array-item properties count), at most 2 nesting levels, and every array needs `items`. |
| `stream` | boolean | Returns SSE (server-sent events, a stream of partial results) only when `outputSchema` is set. Otherwise you get normal JSON. |
| `compliance` | `hipaa` | Enterprise only. |
| Deprecated | `startCrawlDate`, `endCrawlDate` (ignored), `includeText`, `excludeText` (word-level approximate match, up to 50 strings), `context` | Avoid. |

**Response:**
- `requestId`.
- `results[]`. Each result has:
  - `title` and `url` (always present)
  - `id` (pass to /contents)
  - `publishedDate` (an estimate, may be absent)
  - `author` (nullable)
  - `image`, `favicon`
  - `text`, `highlights[]`, `highlightScores[]`, `summary`, `subpages[]`
  - `entities[]` (typed company, person or publication data)
  - `extras{links, imageLinks, richImageLinks[{url,alt}], richLinks[{url,anchor}], codeBlocks[{text,source}]}`
- `costDollars{total, search{neural, keyword}, summary, contents{text, highlights, summary}}`. The spec says billing comes from usage counters, not from this object.
- `searchTime` in ms. It is server-side and may leave out synthesis time.
- `output{content, grounding[]}`, only when `outputSchema` is set.
- `resolvedSearchType` (deprecated, may be `""`).
- `context` (deprecated).

**Entity data (useful for company and people demos):**
- **Company** entities (`type: company`): `properties.name`, `foundedYear`, `description`, `workforce.total`, `headquarters{address, city, postalCode, country}`, `financials{revenueAnnual, fundingTotal, fundingLatestRound{name,date,amount}}`, `webTraffic{visitsMonthly, countryRank, avgDurationSeconds, history[]}`, `research{worksCount, citationCount, areas, notableWorks, topResearchers}`.
- **Person** entities: `name`, `firstName`, `lastName`, `location`, `workHistory[{title, location, dates{from,to}, company{id,name}}]`, `educationHistory[...]`, `research{... hIndex ...}`.
- **Publication** entities: `title`, `year`, `date`, `type`, `language`, `citationCount`, `authors[{name,id}]`, `referenceCount`, `abstract`, `doi`.

Python (exa-py):
```python
from exa_py import Exa
exa = Exa()  # reads EXA_API_KEY
r = exa.search(
    "10-K risk factors that mention dependency on third-party AI models",
    type="auto",
    category="financial report",
    num_results=10,
    contents={"highlights": True},
)
for x in r.results:
    print(x.title, x.url, x.published_date, x.highlights)
print(r.cost_dollars.total if r.cost_dollars else None)
```
Raw HTTP:
```bash
curl -s -X POST https://api.exa.ai/search \
  -H "Content-Type: application/json" -H "x-api-key: $EXA_API_KEY" \
  -d '{"query":"10-K risk factors that mention dependency on third-party AI models","type":"auto","category":"financial report","numResults":10,"contents":{"highlights":true}}'
```

### 2.2 POST /contents

**Request:** send either `ids` or `urls` (1 to 100 items, each up to 2048 characters), never both. The quickstart uses `ids`, while the SDKs send `urls`.

The content options sit at the TOP LEVEL, with no `contents` wrapper:
- `text`, `highlights`, `summary`, `extras`
- `livecrawlTimeout` (ms, default 10000, max 90000)
- `maxAgeHours` (-1 to 720)
- `snapshotAsOf`
- `subpages` (0 to 100), `subpageTarget` (a string or an array of up to 100 strings)
- `compliance`
- Deprecated: `livecrawl`, `crawledBeforeDate`, `context`

**Response:**
- `requestId`, `results[]` (same shape as search results), `costDollars`, `searchTime`.
- `statuses[]`, with `{id, status: success|error, source: cached|crawled, error{tag, httpStatusCode}}`.
- A failure on one URL does not fail the whole request. It shows up as that URL's entry in `statuses`.
- Status tags: `CRAWL_NOT_FOUND`, `CRAWL_HTTP_{status}`, `CRAWL_TIMEOUT`, `CRAWL_LIVECRAWL_TIMEOUT`, `SOURCE_NOT_AVAILABLE`, `UNSUPPORTED_URL`, `CRAWL_UNKNOWN_ERROR`, and `CONTENT_NOT_CACHED` (Snapshot only).

Python:
```python
r = exa.get_contents(
    ["https://www.sec.gov/..."],
    highlights={"query": "revenue guidance"},
    text=False,  # see gotcha 2: exa-py otherwise also adds text
)
print(r.results[0].highlights, r.statuses)
```
HTTP:
```bash
curl -s -X POST https://api.exa.ai/contents -H "Content-Type: application/json" -H "x-api-key: $EXA_API_KEY" \
  -d '{"urls":["https://exa.ai/blog/dynamic-highlights"],"highlights":{"query":"token efficiency"}}'
```

### 2.3 POST /answer

**Request:**
- `query` (required)
- `stream` (boolean)
- `text` (boolean: include each citation's full text)
- `model`: the spec enum is `exa` (default), `exa-pro`, `exa-research`, `exa-fast`. The exa-py type hint lists only `exa` and `exa-pro`.
- `systemPrompt`, `userLocation`
- `outputSchema` (JSON Schema draft 7). If set, `answer` comes back as an object instead of a string.

**Response:** `requestId`, `answer` (string or object), `citations[]{title, url, publishedDate, author, id, image, favicon, text}`, `costDollars`. The stream is OpenAI-style chunks (`choices[].delta.content`) plus separate citations, cost and error chunks.

**Price and limits:** $5/1k. Zero Data Retention (ZDR: Exa stores nothing) is NOT supported for Answer.

Python:
```python
a = exa.answer("What did NVIDIA guide for next-quarter revenue?", text=False)
print(a.answer); print([c.url for c in a.citations])
for chunk in exa.stream_answer("Explain the CHIPS Act"):
    print(chunk.content or "", end="")
```
HTTP (built from the spec, not copied from a docs sample):
```bash
curl -s -X POST https://api.exa.ai/answer -H "Content-Type: application/json" -H "x-api-key: $EXA_API_KEY" \
  -d '{"query":"What did NVIDIA guide for next-quarter revenue?"}'
```

### 2.4 POST /findSimilar (deprecated)

- **Request:** `url` (required, min 3 characters), `numResults`, domain and date filters, `category`, `excludeSourceDomain` (boolean), `contents`. There is no `type` field.
- **Deprecation:** the spec marks it `deprecated: true` and the response carries a `Deprecation` header. exa-py wraps `find_similar()` in `@deprecated`, with the migration advice `search("pages similar to " + url)`.
- The Python example below is built from the SDK signature; I found no docs sample.

```python
exa.find_similar("https://example.com/post", num_results=5, exclude_source_domain=True, contents={"highlights": True})
```

### 2.5 Exa Agent: /agent/runs (replaces the old Research API's role)

**Create request:**
- `query` (required), `systemPrompt`.
- `effort`: `minimal`, `low`, `medium`, `high`, `xhigh`, `auto` (DEFAULT), `ultra`.
- `input{data[], exclusion[]}`: rows to enrich, and records to leave out.
- `outputSchema`: any JSON Schema (draft-07, 2019-09 or 2020-12). Unlike Search, the docs set no 10-property cap here.
- `previousRunId`: continue from a completed run.
- `metadata`: a string-to-string map.
- `dataSources`: up to 5 providers from `fiber`, `financial_datasets`, `similarweb`, `baselayer`, `affiliate`, `particle`, `jinko`, `polymarket`, `macrobond`.
- `budget{maxCostDollars ($1 to $100, auto and ultra only), maxDurationSeconds (300 to 10,800, ultra only)}`.

**Run object:**
- `id` (prefix `agent_run_`), `object: "agent_run"`.
- `status`: `queued`, `running`, `completed`, `failed`, `cancelled`.
- `stopReason`: `schema_satisfied`, `budget_reached`, `time_limit_reached`, `stopped`, `error`, `cancelled`.
- `createdAt`, `completedAt`, `request`.
- `output{text, structured, grounding[{field, citations[{url,title}], confidence: low|medium|high|null}]}`.
- `usage{agentComputeUnits, searches, emails, phoneNumbers, dataSources}`.
- `costDollars{total, agentCompute, search, emails, phoneNumbers, dataSources}`.

**Error codes:** `CONCURRENCY_LIMIT_REACHED`, `INVALID_OUTPUT_SCHEMA`, `INVALID_DATA_SOURCE`, `PREVIOUS_RUN_NOT_FOUND`, `PREVIOUS_RUN_NOT_COMPLETED`, `RUN_NOT_FOUND`, `TIMEOUT`, `SERVER_ERROR`, and others.

**SSE events:** `agent_run.created`, `agent_run.started`, `agent_run.completed`, `agent_run.failed`, `agent_run.cancelled`. The docs also mention `agent_run.source.added`, a live preview of sources, and tell you to ignore event names you don't recognize.

Python:
```python
run = exa.agent.runs.create(
    query="Find up to 10 US regional banks that disclosed commercial real estate losses in their latest 10-Q.",
    effort="medium",  # fixed $0.10; omit and you get metered auto with a $5 cap
    output_schema={"type": "object", "required": ["banks"], "properties": {"banks": {"type": "array", "maxItems": 10, "items": {"type": "object", "required": ["name", "ticker"], "properties": {"name": {"type": "string"}, "ticker": {"type": "string"}, "detail": {"type": ["string", "null"]}}}}}},
)
run = exa.agent.runs.poll_until_finished(run.id, poll_interval=4000)  # milliseconds
print(run.output.structured, run.output.grounding, run.cost_dollars)
```
HTTP:
```bash
curl -s -X POST https://api.exa.ai/agent/runs -H "Content-Type: application/json" -H "x-api-key: $EXA_API_KEY" \
  -d '{"query":"...","effort":"medium"}'
curl -s https://api.exa.ai/agent/runs/$RUN_ID -H "x-api-key: $EXA_API_KEY"
# live stream instead of polling: add -H "Accept: text/event-stream" to the POST
```

**SDK methods:**
- exa-py: `exa.agent.runs.create / get / list / list_all / cancel / stop / delete / poll_until_finished / create_and_wait`.
- exa-js: `exa.agent.runs.create`, `pollUntilFinished(id, {pollInterval, timeoutMs})`.

### 2.6 Monitors: /monitors

**Create request:**
- `name`.
- `search{query (required), numResults 1 to 100, includeDomains, excludeDomains, contents}` (required).
- `trigger{type: "interval", period: "1h" | "6h" | "1d" | "7d" ...}`. The minimum is 1 hour. Omit `trigger` for a manual-only monitor.
- `outputSchema` (text or object).
- `metadata`, which is echoed back in webhooks.
- `webhook{url, events[]}` (required). `url` must be HTTPS and "must not point to localhost or private IP ranges". `events` can include `monitor.created`, `monitor.updated`, `monitor.deleted`, `monitor.run.created`, `monitor.run.completed`.

**Behavior:**
- `webhookSecret` is returned once, at creation.
- Run statuses: `pending`, `running`, `completed`, `failed`, `cancelled`.
- A completed run holds `output.results`, `output.content` and `output.grounding`.
- Runs can be up to 30 minutes late and never overlap.
- `POST /monitors/{id}/trigger` runs one immediately, so you can demo it without waiting for the schedule.

Python (the docs pass a camelCase dict here):
```python
m = exa.monitors.create({"name": "CRE stress", "search": {"query": "regional bank commercial real estate loan loss disclosures"}, "trigger": {"type": "interval", "period": "1d"}, "webhook": {"url": "https://your-public-endpoint/hook", "events": ["monitor.run.completed"]}})
exa.monitors.trigger(m.id); print(exa.monitors.runs.list(m.id, limit=1).data[0].status)
```
HTTP: `POST https://api.exa.ai/monitors` with the same body.

### 2.7 Batch API (Enterprise, beta)

- Needs the header `Exa-Beta: batches-2026-06-06` on every call.
- Each item has `customId` (1 to 64 characters, unique within the batch), `method: "POST"`, `url` (`/search` or `/agent/runs`), and `body` (`stream: true` is not allowed).
- Statuses: `in_progress`, `completed`, `cancelling`, `cancelled`, `expired`.
- `resultsUrl` is a short-lived presigned link (a download URL that expires) to a JSONL results file.
- Not available on free or pay-as-you-go plans; Exa must enable it for your team.

### 2.8 OpenAI-compatible surfaces

**`/chat/completions`:** point the OpenAI SDK at `base_url="https://api.exa.ai"` with `model="exa"`. Pass `/answer` fields through `extra_body`. Citations appear at `message.citations`.

**`/responses`:** use `model="exa-agent"`, with `reasoning.effort` set to any of the Agent effort levels.
- Three modes: synchronous, `stream: true`, or `background: true`.
- `high`, `xhigh` and `ultra` in synchronous mode return a 400, so use stream or background for those.
- There is no `budget` field.
- Use `previous_response_id` to continue a run.

## 3. Search types and latency

| `type` | Use | Latency (docs quickstart and pricing page) | Price per 1k |
|---|---|---|---|
| `instant` | autocomplete, voice, real-time | about 250 ms | $4 |
| `fast` | latency-sensitive, user-facing | about 450 ms | $7 |
| `auto` (default) | best general balance | about 1 s | $7 |
| `deep-lite` | light research plus synthesis | about 4 s | $12 |
| `deep` | multi-step search, structured lists | 4 to 15 s | $12 |
| `deep-reasoning` | hardest synthesis (the old /research replacement) | 12 to 40 s | $15 |

**Notes:**
- `outputSchema` adds about 2 s of synthesis.
- `contents.maxAgeHours: 0` adds a live page fetch.
- Deep types are limited to 5 QPS (queries per second) instead of 10.
- Deep types are the recommended default when you use `outputSchema` for more than about two items or three or more fields.
- `neural` and `keyword` are NOT in the current API enum. exa-py still lists `neural`, and exa-js still lists `keyword`, `neural` and `hybrid`. See the uncertainties.

**Exa's own latency numbers disagree between pages:**
- Product page (exa.ai/products/search): Instant 323 ms, Fast 450 ms (454 ms in the benchmark), Auto about 1.2 s, Deep 4 to 12 s (4.3 s average).
- Enterprise page (exa.ai/enterprise): Instant P50 178 ms.
- Feb 2026 changelog: Instant "sub-150ms".

**Benchmark on the product page (accuracy / latency):**
- Exa Instant 63.6% / 323 ms
- Exa Fast 69.6% / 454 ms
- Exa Auto 67.8% / about 1.2 s
- Exa Deep 80.0% / 4.3 s
- Parallel (Adv) 46.0% / 2.7 s
- Brave 43.0% / 547 ms
- Perplexity 50.0% / 583 ms

## 4. Filters

- **Domains:** `includeDomains` and `excludeDomains` (max 1200 each) accept hostnames, path prefixes (`anthropic.com/news`) and wildcards (`*.substack.com`). An exa-py code comment calls the two "exclusive" (not usable together), but the spec does not say so.
- **Dates:** `startPublishedDate` and `endPublishedDate` take ISO 8601 values. An exa-py comment says pages with no detected date are excluded when you use these filters. The crawl-date fields are ignored.
- **Categories (the full current list):** `company`, `publication`, `news`, `personal site`, `financial report`, `people`.
  - `company` and `people` reject `startPublishedDate`, `endPublishedDate` and `excludeDomains` (400).
  - Snapshot does not support `category`.
- **Text include/exclude:** `includeText` and `excludeText` are deprecated. They matched approximately at word level, took up to 50 strings of up to 4096 characters each, and are ignored on /findSimilar entity categories. Exa's advice is to put the terms in the query instead.
- **Result count:** `numResults` goes from 1 to 100 (default 10). Tags `INVALID_NUM_RESULTS` (more than 100 with highlights) and `NUM_RESULTS_EXCEEDED` (over your plan's limit) exist. The Enterprise card advertises "Up to 1,000 results per search, requests above 25 results".
- **Other:** `userLocation` and `moderation`.
- **Language:** since Nov 2025, results are automatically filtered to the language of your query.
- **Freshness (not a filter):** `contents.maxAgeHours` controls how fresh the extracted page content is. It does not filter by publication date.

## 5. Contents options (inside `contents` on /search, top level on /contents)

- **`text`:** `true`, or an object with:
  - `maxCharacters` (1 to 1,000,000)
  - `includeHtmlTags` (default false; output is clean markdown otherwise)
  - `verbosity` (`compact` default, `standard`, `full`)
  - `includeSections` / `excludeSections`, from `header`, `navigation`, `banner`, `body`, `sidebar`, `footer`, `metadata`. This is best-effort.
  - The rendering options apply to newly fetched pages only when you also set `maxAgeHours: 0`.
- **`highlights`:** `true` (Exa's recommended default: excerpts sized to how relevant each page is), or an object with:
  - `query` (steers which passages are picked)
  - `maxCharacters` (a fixed limit per page)
  - `dynamic: true`: the Dynamic Highlights research preview, which shares one context budget across all results. Not compatible with maxCharacters. Needs the header `Exa-Beta: dynamic-highlights-2026-08-28`, or `betas=[DYNAMIC_HIGHLIGHTS_BETA]` in the SDKs.
  - `verbosity` (`low`, `medium`, `high`; beta, needs the same header)
  - Deprecated: `numSentences` (mapped to about 1333 characters per sentence) and `highlightsPerUrl` (ignored).
- **`summary`:** `{query, schema}`. This is one LLM call per page at $1/1k pages. With `schema`, the summary comes back as a JSON STRING that you must parse.
- **`extras`:** `links`, `imageLinks`, `richImageLinks`, `richLinks`, `codeBlocks`, each 0 to 1000 per page.
- **Freshness:**
  - `maxAgeHours`: omit it to use cache with a fetch fallback; a positive number means "fetch if the cached copy is older than N hours"; `0` always fetches; `-1` uses cache only; the maximum is 720.
  - `livecrawlTimeout`: ms, default 10000, max 90000. The docs suggest 12000 to 15000 for slow sites.
  - Old `livecrawl` mapping: `always` becomes `maxAgeHours: 0`, `never` becomes `-1`, `fallback` means omit it, and `preferred` roughly becomes `1`. Never send `livecrawl` and `maxAgeHours` together.
- **Subpages:** `subpages` (0 to 100) and `subpageTarget` (for example `["pricing", "investors"]`).
- **Snapshot:** `snapshotAsOf` returns the version of the page Exa had stored at a past time (ISO date or date-time).
  - Rolling 5-month window, 10 QPS on pay-as-you-go, and "After 100 requests, talk to sales".
  - Supports only `auto`, `fast` and `instant`, with no `category`.
  - Cannot be combined with `livecrawl`, `livecrawlTimeout`, `maxAgeHours` or `subpages` (`INVALID_REQUEST`).
- **Billing:** pick one view per request. text, highlights and summary are each billed separately on /contents. On /search, contents for the first 10 results are included in the base price.

## 6. Structured output and citations

| Where | How you ask | What comes back | Citations |
|---|---|---|---|
| /search | `outputSchema` (text or object; max 10 properties, 2 levels, works with every type) plus optional `systemPrompt` | `output.content` | `output.grounding[{field (e.g. companies[0].amount), citations[{url,title}], confidence low/medium/high}]`. Do not add citation or confidence fields to your own schema. |
| /search streaming | `stream: true` plus `outputSchema` | SSE chunks typed `text-delta`, `grounding`, `results`, `stream-reset`, `done`, `error`, ending with `data: [DONE]` | grounding chunks |
| /answer | plain, or `outputSchema` (draft 7) | `answer` (string or object) | `citations[]` (the source list, not per-field) |
| /contents or /search summary | `summary.schema` | a JSON string in `summary` | none beyond the page itself |
| Agent | `outputSchema` (any JSON Schema, draft-07, 2019-09 or 2020-12) | `output.structured` (fields may be `null` when evidence is missing), plus `output.text` | `output.grounding` per field, with confidence |
| Monitors | `outputSchema` | `output.content` | `output.grounding` |
| Websets | criteria plus enrichments | `evaluations[{criterion, reasoning, satisfied, references}]`, `enrichments[{result, reasoning, references}]` | `references` |

## 7. Websets, the Research API, and what to use in a 10-minute live demo

**Research API:** retired 2026-04-01 and replaced by `type: "deep-reasoning"`. Both SDKs still ship an `exa.research` client that calls `/research/v1` (exa-py models: `exa-research-fast`, `exa-research`, `exa-research-pro`). Do not build on it.

**Websets:**
- Asynchronous. You create one, then poll or receive webhooks.
- The docs say: "Starting a new list-building or enrichment workflow? Use Exa Agent." Use Websets "to maintain or extend an existing Websets integration."
- "The Websets API requires a paid Websets plan; Search API credits and Websets credits are separate."
- The Free plan caps a webset at 25 verified results.
- "Small websets finish in minutes"; 1,000+ items take much longer.
- Credit prices sit behind https://websets.exa.ai/billing. They are not on the public pricing page; I checked the `?tab=websets` view and it showed nothing.
- ZDR is not supported.
- Rate limit 20 QPS, plus plan-based concurrency, which you can check with `GET /v0/teams/me`.

**Exa Agent:**
- Asynchronous. The docs say runs take "seconds to minutes".
- Fixed efforts cost $0.012, $0.025, $0.10, $0.50 or $1.00 per run.
- `auto` (the default) is metered at $0.10 per ACU (Agent Compute Unit, Exa's unit of model computation), $0.005 per search, $0.02 per email and $0.07 per phone number, with a $5 cap by default. `ultra` is metered with a $20 cap.
- Ultra "typically" takes about 30 minutes and can take up to 3 hours.
- The docs give no latency numbers for fixed efforts.
- Concurrency is 50 active runs, at 5 QPS. Each create counts as 2 requests. Polling GETs do not count against QPS.

**Practical verdict for a 10-minute live slot (my judgment, not Exa's):**
- The live parts should be `/search` (`auto` or `fast` with highlights) and `deep` with `outputSchema`, which returns field-level citations in 4 to 15 s.
- An Agent run at `low` or `medium` fixed effort is a reasonable live finale if you stream the events. Have a completed run ID ready as a fallback, and retrieve it with `GET /agent/runs/{id}` (non-ZDR teams only).
- Websets and Agent `ultra` should be pre-run and shown as results, not run live.
- Monitors can be shown with `POST /monitors/{id}/trigger`. The webhook must be a public HTTPS URL.

## 8. Pricing, free credits, key, rate limits

**Free tier:**
- "$10 in credits (up to 2,500 Instant searches) the day you sign up". The free balance resets to $10 on the 1st of each month and does not accumulate.
- A one-time $10 bonus comes after completing dashboard onboarding.
- No payment method is required.
- Only a user's first team gets the monthly grant.

**Pay-as-you-go:** prepaid credits, no subscription and no minimum. Buying $1,000 of credits within any 30 days raises you to 25 QPS for 90 days.

**Rates (from docs /admin/pricing, matching exa.ai/pricing):**
- Search: `instant` $4/1k; `fast` and `auto` $7/1k; `deep-lite` and `deep` $12/1k; `deep-reasoning` $15/1k. The base covers 10 results.
- Each extra result: $1/1k.
- AI page summaries: $1/1k pages.
- /contents: $1/1k pages per content type.
- /answer: $5/1k.
- /monitors: $15/1k.
- Agent: as in section 7.
- Exa Connect providers cost extra. Examples: Fiber $0.02/credit, Similarweb $0.30/credit, Polymarket and Macrobond free, Financial Datasets $0.01/call.

**Rate limits (defaults, per team, across all keys):**
- `/search`, `/answer` and `/chat/completions`: 10 QPS.
- Deep search types: 5 QPS.
- `/contents`: 100 QPS.
- `/agent/runs` and `/responses`: 5 QPS and 50 active runs.
- `/websets/*`: 20 QPS.
- Going over returns 429. Honor `Retry-After` when present.

**Other plan limits:**
- The MCP keyless tier is 3 QPS and 150 calls per day (from the Feb 2026 changelog).
- A 402 means credits are exhausted or a key budget was hit (`NO_MORE_CREDITS`, `API_KEY_BUDGET_EXCEEDED`, `TEAM_BUDGET_EXCEEDED`).

**Key and dashboard links:**
- Key: https://dashboard.exa.ai/api-keys
- Billing: https://dashboard.exa.ai/billing
- Playground: https://dashboard.exa.ai/playground/search
- Onboarding: https://dashboard.exa.ai/onboarding

**Cost arithmetic for demo prep (mine, from the rates above):**
- 100 `auto` searches with highlights cost about $0.70.
- 100 `deep` searches cost about $1.20.
- 10 `medium` Agent runs cost $1.00.
- One `auto` Agent run with no budget can use up to $5, which is half the monthly free grant.

## 9. SDKs and MCP

**Python:**
- `pip install exa-py` (or `uv add exa-py`); import with `from exa_py import Exa, AsyncExa`.
- Latest on PyPI: **2.22.2** (uploaded 2026-09-21). Requires Python 3.9 or later.
- Main methods: `search`, `stream_search`, `get_contents`, `answer`, `stream_answer`, `find_similar` (deprecated), `agent.runs.*`, `monitors.*`, `websets.*`, `research.*` (dead endpoint).
- Tool-calling helpers: `exa.openai.web_search()`, `exa.anthropic.web_search()` / `get_contents()` / `handle_tool_use()`, and `exa.wrap(openai_client)`.

**JavaScript:**
- `npm install exa-js` (or `pnpm add exa-js`); `import Exa from "exa-js"`.
- Latest on npm: **2.23.0** (2026-09-24).
- Methods: `search`, `streamSearch`, `getContents`, `answer`, `streamAnswer`, `findSimilar` (deprecated), `agent.runs.*`, `monitors.*`, `websets.*`.
- TypeScript types such as `SearchResponse` and `RegularSearchOptions` are included.

**Other packages:**
- `@exalabs/ai-sdk` 2.1.0 (Vercel AI SDK).
- Agent skills: `npx skills add exa-labs/agent-skills`.

**MCP (Model Context Protocol, the standard way for AI assistants to call outside tools):**
- Hosted at `https://mcp.exa.ai/mcp`. Open source at github.com/exa-labs/exa-mcp-server; the npm package is `exa-mcp-server` 3.4.1.
- Auth modes: keyless (free rate limits), OAuth via `https://mcp.exa.ai/mcp?login`, or the `x-api-key` header.
- Tools: `web_search_exa` and `web_fetch_exa` (on by default), `web_search_advanced_exa` (opt-in), `agent_run` (on by default once authenticated).
- Choose tools with `?tools=web_search_exa,web_fetch_exa,web_search_advanced_exa,agent_run`. An explicit list replaces the defaults.
- Local version: `npx -y exa-mcp-server` with the `EXA_API_KEY` env var.
- Claude Code install: `claude plugin install exa@claude-plugins-official`.

## 10. Enterprise features (what a buyer will ask)

**Security and compliance:**
- **SOC 2 Type II:** docs security overview. Reports, DPA and other documents live at https://trust.exa.ai. That page did not render any content when I fetched it.
- **Zero Data Retention:** Enterprise, enabled per team. Available for Search, Contents and Agent; not for Answer or Websets. For Agent under ZDR:
  - run data lasts only 10 minutes after the run ends
  - no `previousRunId`
  - no Connect `dataSources`
  - no event replay
- **HIPAA mode:** `compliance: "hipaa"` on /search and /contents only. It requires `type` `instant` or `fast`, text or highlights (no summary), and cache-only reads. A BAA (the contract HIPAA requires) is available. A team without it enabled gets 403 `FEATURE_DISABLED`.
- **Regional blocking:** Crimea, Cuba, Iran, North Korea, Russia, Syria, Ukraine and Venezuela are blocked, possibly by a Cloudflare page rather than an Exa JSON error.

**Commercial:**
- Enterprise pricing card: up to 1,000 results per search, custom QPS, tailored moderation, custom indexes, SLAs and MSAs, 1:1 onboarding, volume discounts, postpaid invoicing.
- The exa.ai/enterprise page also claims:
  - GDPR, CCPA and HIPAA with BAA
  - "Your queries and results are never stored or trained on" (under ZDR)
  - forward-deployed engineers, custom data indexing, and configuration of throughput, region and retrieval behavior
  - committed-use plans
  - named customers: monday.com, HubSpot, Cognition, CodeRabbit, OpenRouter, 11x; testimonials from AWS, Klarna, Groq, Databricks, Cursor
  - "Exa powers all parts of Devin" (Walden Yan, Cognition)
- The products page lists Cursor, Cognition, HubSpot, Monday.com, Sarvam and OpenRouter.

**Governance and scale:**
- Per-key budgets (`budgetCents`) and rate limits through the Team Management API or the dashboard.
- Batch API.
- Snapshot, for reproducible evaluations and backtests.
- **Index facts (FAQ, as of August 2026):** the index tracks 1.4 trillion URLs and serves 100 billion pages. The crawler is `ExaSearchBot` and respects robots.txt. The News page says new articles are searchable within minutes of publication.

## 11. Known gotchas

1. **Content options live in different places per endpoint.** On `/search` they go inside `contents`; on `/contents` they sit at the top level. Putting top-level `text`, `highlights` or `summary` on /search is one of Exa's listed common mistakes.
2. **exa-py silently adds full text.**
   - `search()` with no `contents` sends `text: {maxCharacters: 10000}`. Pass `contents=False` for titles and URLs only.
   - `get_contents()` adds `text` (10k characters) whenever you pass no `text`, `summary` or `extras`, even if you asked for `highlights`. That means two content types billed on /contents. Pass `text=False`.
   - exa-js `search()` has the same default, but `getContents()` does NOT add text.
3. **Python is snake_case all the way down.** Nested keys too (`contents={"max_age_hours": 24}`, `num_results`, `output_schema`, `system_prompt`). The SDK converts keys to camelCase, except inside `output_schema` and `schema`. The docs' monitors example, however, passes a camelCase dict (`"numResults"`) to `exa.monitors.create`.
4. **exa-py validates option names strictly.** An unknown key raises `ValueError("Invalid option: ...")` before any request is made.
5. **Streaming needs the stream helpers.** `search(..., stream=True)` and `answer(..., stream=True)` raise in the SDKs; use `stream_search` / `stream_answer` (`streamSearch` / `streamAnswer` in JS). Over raw HTTP, `/search` streams only when `outputSchema` is set.
6. **`outputSchema` limits on Search:** 10 properties in total, 2 nesting levels, every array needs `items`. Otherwise you get a 400 (`output_schema exceeds maximum of 10 properties`). For wider tables, use Agent.
7. **Agent `effort` defaults to metered `auto`, capped at $5.** Set a fixed effort or `budget.maxCostDollars` for predictable cost. `create_and_wait` in exa-py times out after 120,000 ms by default; `poll_until_finished` after 1 hour. exa-py `poll_interval` is in milliseconds.
8. **Agent may return `null` for required fields,** and `schema_satisfied` does not guarantee strict validation. Make fields nullable and persist `output.grounding`.
9. **Deprecated but still in the SDKs:** `exa.research` (dead /research endpoint), `find_similar`, `start_crawl_date` / `end_crawl_date` (ignored), `include_text` / `exclude_text`, `livecrawl`, `context`, `num_sentences` / `highlights_per_url`, and `use_autoprompt` (removed). exa-js `searchAndContents` is deprecated in favor of `search`.
10. **Docs and SDKs disagree in places:**
    - `additionalQueries`: the spec allows up to 10, the exa-py docstring says "Max 5".
    - `type`: the spec enum lacks `neural` and `keyword`, but exa-py lists `neural` and exa-js lists `keyword`, `neural` and `hybrid`.
    - `answer` `model`: the spec lists 4 values, the exa-py type hint lists 2.
    - Stale exa-py comments: `resolved_search_type` "'neural' or 'keyword'", and `num_results` "Max for basic: 10".
    - `highlightScores`: the changelog says it was removed on May 1, 2026, but the spec still lists it.
    - `resolvedSearchType` may be an empty string. Do not branch on it.
11. **exa-py drops the per-URL error details on /contents.** Its `ContentStatus` keeps only `id`, `status` and `source`, so to see why a URL failed you need raw HTTP.
12. **`publishedDate` is an estimate** parsed from the page and may be missing. The docs' "Example response" shows results without it.
13. **`company` and `people` categories reject date filters and `excludeDomains`** (400). Snapshot rejects `category` and the deep types.
14. **Monitors' webhook** must be a public HTTPS URL, not localhost or a private IP. `webhookSecret` is shown only once.
15. **Batch needs an Exa-Beta header** and Enterprise enablement. Dynamic Highlights needs its own beta header.
16. **CORS:** a preflight check from `Origin: http://localhost:3000` returned `access-control-allow-origin` for that origin and allowed `x-api-key`. CORS is the browser rule that decides whether a web page may call another site directly, so a browser page can call Exa directly. That would expose your API key, so proxy through a small server (my recommendation).
17. **`costDollars` in responses is an estimate.** Billing uses usage counters. Log `requestId`, `searchTime` and `costDollars` anyway.
18. **A 503 `SERVICE_OVERLOADED` is not billed.** Retry it with backoff; lowering your request rate does not help.

## 12. Suggested demo-safe defaults (my recommendations)

- **Server-side calls only:** Python, FastAPI or Streamlit, or a Next.js API route.
- **Search default:** `type="auto"`, `contents={"highlights": True}`, `num_results=10`.
- **"Research" button:** `type="deep"` with a 4 to 8 property `outputSchema`. Render `output.grounding` as clickable per-field citations with their confidence.
- **Contents:** `get_contents(urls, highlights={"query": ...}, text=False)`.
- **Agent:** `effort="low"` or `"medium"`, streamed events, one pre-completed run ID cached as a fallback.
- **Freshness:** set `maxAgeHours` only for prices or quotes.
- **Safety net:** set a per-key budget in the dashboard, and handle 429 and 503 with backoff.

## Sources (all fetched 2026-09-29)
- https://docs.exa.ai/llms.txt (index; docs.exa.ai redirects to https://exa.ai/docs) and https://docs.exa.ai/llms-full.txt
- https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml
- https://exa.ai/docs/index.md, /get-started/quickstart.md, /get-started/exa-mcp.md
- https://exa.ai/docs/search/quickstart.md, /search/deep-search.md, /search/highlights.md, /search/snapshot.md, /search/best-practices.md, /search/data/overview.md, /search/data/financial.md, /search/data/companies-people.md, /search/data/news.md
- https://exa.ai/docs/contents/quickstart.md, /reference/search.md, /reference/get-contents.md, /reference/answer.md
- https://exa.ai/docs/agent/quickstart.md, /agent/best-practices.md, /agent/agent-ultra.md, /agent/connect/overview.md
- https://exa.ai/docs/monitors/quickstart.md, /batch/quickstart.md, /websets/quickstart.md, /websets/api/teams/get-team-info.md
- https://exa.ai/docs/sdks/quickstart.md, /integrations/openai-sdk.md, /integrations/tool-calling/anthropic.md
- https://exa.ai/docs/admin/pricing.md, /admin/billing.md, /admin/security/overview.md, /admin/security/zero-data-retention.md, /admin/security/hipaa.md, /admin/status.md, /admin/error-codes.md, /admin/faqs.md, /changelog.md
- https://exa.ai/pricing, https://exa.ai/pricing?tab=websets (no Websets content rendered), https://exa.ai/products/search, https://exa.ai/enterprise, https://exa.ai/blog/exa-agent, https://trust.exa.ai (content did not render)
- SDK source: https://raw.githubusercontent.com/exa-labs/exa-py/master/exa_py/api.py, .../exa_py/agent/client.py, .../exa_py/research/base.py and sync_client.py, https://raw.githubusercontent.com/exa-labs/exa-js/master/src/index.ts
- Versions: https://pypi.org/pypi/exa-py/json, https://registry.npmjs.org/exa-js, https://registry.npmjs.org/exa-mcp-server, https://registry.npmjs.org/@exalabs/ai-sdk