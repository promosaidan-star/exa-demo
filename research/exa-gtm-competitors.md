# Exa: company, go-to-market and competition (as of 2026-09-29)

Scope note: everything below comes from pages I actually loaded today. Where a number comes from Exa's own marketing (especially its "Exa vs X" comparison pages), I say so, because vendor benchmarks are self-graded. Pages that would not load are listed at the end.

## 0. The short version for the demo

- Exa sells a web search API built for AI agents, not for humans. Its pitch has three parts: (1) it runs its own index instead of reselling Google or Bing, (2) it is fast and returns only the relevant passages ("highlights"), so the customer's LLM reads fewer tokens, and (3) it has dedicated indexes for people, companies, research papers, code and financial data.
- In the last 12 months Exa moved "up the stack" from a search call to agents: Deep search, then Monitors (scheduled searches with webhooks), then Exa Agent (multi-step research that returns structured tables), then Exa Connect (paid data partners inside the agent), then Agent Ultra (last week).
- Go-to-market is shifting from self-serve developers to enterprise sales: a $250M Series C in May 2026, a new CRO from LaunchDarkly, and roughly 20 GTM roles open (AEs, SDRs, FDEs in NYC, London and Singapore, a first VP of post-sales, a deal desk, a technical enablement manager).
- The competitive field is crowded and the benchmarks conflict. Exa's own pages show Exa winning almost everything; Parallel's own page shows Parallel winning; the one independent benchmark I found (AIMultiple) has Brave, Firecrawl, Exa and Parallel statistically tied. The honest winning ground for Exa is entity search (people and companies), publication search, low latency, token efficiency, and breadth of one API.

## 1. Company basics

**Founders and history**
- Will Bryk (CEO) and Jeff Wang (co-founder). Both Harvard; Bryk previously an engineer at Cresta, Wang built data infrastructure at Plaid (exa.ai/about).
- Started in 2021; first search engine launched November 2022 (Series B blog). Formerly named Metaphor; renamed Exa on January 25, 2024 ("exa" as in 10 to the 18th) (exa.ai/blog/announcing-exa).
- a16z says the founders built a search engine together at Harvard about a decade ago (a16z.com/announcement/investing-in-exa).

**Funding**

| Round | Date | Amount | Valuation | Lead | Others |
|---|---|---|---|---|---|
| Seed + Series A | Jul 16, 2024 | $22M combined | not stated | Lightspeed | NVentures (NVIDIA), Y Combinator |
| Series B | Sep 3, 2025 | $85M | $700M | Benchmark (Peter Fenton joined board) | Lightspeed, YC, NVentures |
| Series C | May 20, 2026 | $250M | $2.2B | a16z | Benchmark, Lightspeed, YC; press reports angels incl. Scott Wu, Igor Babuschkin, Tal Broda |

My sum of the three announced rounds is about $357M. Getlatka's "$335M" total does not match that sum.

**Headcount and offices**
- About 100 people per the FDE postings (Aug 2026); the Forward Deployed PM posting published Sep 26, 2026 says about 150. Treat headcount as 100 to 150 and growing fast (55 open roles on the Ashby board today).
- HQ San Francisco. Singapore office opened March 30, 2026 (engineering, APAC time zone). In-person roles posted in New York City (FDE, AEs, SDRs, SDR manager, field events, commercial counsel) and London (FDE EMEA, field events EMEA).

**Usage and revenue**
- Series C blog (May 2026): 400,000+ developers and 5,000+ companies; named users Cursor, Cognition, HubSpot, OpenRouter, monday.com. The enterprise page today says 500,000+ developers and shows logos including Databricks, AWS, Klarna and Groq.
- Index: about page says 500B+ web pages; the docs FAQ says that as of August 2026 the index tracks 1.4 trillion URLs and serves 100 billion pages. Compute: "hundreds of H200s" (about page).
- Revenue is not published by Exa. Third-party estimates only: Sacra estimated $10M ARR in September 2025 (about 11x year over year, up from about $0.9M); ARR Club lists $12M ARR in January 2026. (ARR = annual recurring revenue, the yearly run rate of subscription or usage revenue.)
- Pricing model is pure usage-based (pay per request), with enterprise volume contracts. The VP Customer Experience posting says the business has consumption-based revenue and that net dollar retention (how much existing customers' spend grows year over year) will be the headline post-sales metric.

**GTM leadership and signals**
- Marcus Holm (formerly President of LaunchDarkly) joined as Chief Revenue Officer with the Series C.
- Open GTM roles signal the motion: AE (SF and NYC, $200K to $450K OTE bands), SDRs, Head of Cloud Partnerships, Deal Desk Manager, Revenue Insights Manager, Technical Enablement Manager, VP Customer Experience (first post-sales leader, owns onboarding, health scores, renewals, support), Forward Deployed PM.
- Target industries named on the enterprise page: software engineering, go-to-market, finance (SEC filings, earnings calls), scientific research, healthcare, legal. The VP CX posting names regulated industries like financial services. The Series B blog named private equity and consulting firms and "large financial firms".
- Google partnership (April 28, 2026): "Grounding with Exa web search" inside Google's Gemini Enterprise Agent Platform, and Exa Agent as a launch partner on the Gemini Enterprise Agent Marketplace. Google's doc page (updated 2026-09-28) says the customer brings an Exa API key, pays Exa at Exa's rates plus Gemini token costs, default quota 200 prompts per minute.

## 2. Product timeline, October 2025 to September 2026

Source for dated items: exa.ai/docs/changelog unless noted.

| Date | What happened |
|---|---|
| Oct 28, 2025 | Breaking SDK release: search returns page contents by default; highlights removed from SDKs (restored in JS on Nov 26); `use_autoprompt` deprecated |
| Nov 5, 2025 | Automatic query-language detection and filtering |
| Nov 20, 2025 | Exa Deep (`type="deep"`): query expansion, parallel searches, per-result summaries |
| Dec 19, 2025 | People Search over 1B+ public profiles; `linkedin` category replaced by `people` |
| Jan 13, 2026 | exa-d data framework (blog) |
| Jan 21, 2026 | Company Search with typed company data (headcount, HQ, financials, traffic) |
| Feb 2, 2026 | `maxAgeHours` replaces the old `livecrawl` switch (freshness control); highlights `maxCharacters`; free unauthenticated MCP tier (3 queries/second, 150 calls/day) |
| Feb 5, 2026 | Exa Instant (`type="instant"`), sub-150ms search for chat, voice and coding agents |
| Mar 3, 2026 | Pricing overhaul: contents for first 10 results bundled into the search price |
| Mar 4, 2026 | Deep revamp: new `deep-reasoning` type (12 to 50s), structured outputs with field-level citations and confidence, Deep 20% cheaper |
| Mar 23, 2026 | WebCode eval for coding agents (blog) |
| Mar 30, 2026 | Monitors API (scheduled searches, deduplicated, webhook delivery); Singapore office |
| Apr 1, 2026 | Deprecations: `/research` endpoint retired (use `/search` with `deep-reasoning`); `resolvedSearchType` and `highlightScores` removed May 1; `startCrawlDate`/`endCrawlDate` silently ignored from Apr 15 |
| Apr 28, 2026 | Google Cloud partnership (grounding + Agent Marketplace) |
| May 20, 2026 | Series C, new CRO |
| Jun 16, 2026 | Exa Agent API (natural-language task, effort levels, `outputSchema` for structured tables, can extend an existing dataset) |
| Jun 24, 2026 | Exa Connect: premium data partners callable inside an Agent run (Similarweb, Fiber.ai, Baselayer, Financial Datasets, Affiliate.com, Particle, Jinko; later Polymarket and Macrobond; on request Crunchbase, ZoomInfo, Harmonic, Definitive Healthcare and others) |
| Jul 1, 2026 | Exa Agent and Connect available through Exa MCP (usable from Claude, Cursor, etc.) |
| Jul 23, 2026 | Publication search over 350M papers; `publication` category replaces `research paper`; `pdf`, `github`, `tweet` categories being deprecated |
| Aug 28, 2026 | Dynamic Highlights (research preview): picks excerpts across the whole result set; Exa reports about 49% better token efficiency in single-turn RAG |
| Sep 24-25, 2026 | Agent Ultra: highest-effort agent for big list building and exhaustive research; metered, default $20 cap per run, 5 minute to 3 hour time budgets, can stop early and keep results |

Live in the docs but with no changelog date I could find: Exa Snapshot (pin search to a stored version of a page at a past datetime, rolling 5-month window, for backtests and reproducible evals), Batch API, Exa in Slack, Exa for Google Sheets, HIPAA mode, pay-per-request via x402/MPP crypto rails, Enterprise Managed Auth for Claude.

**Renamed or retired, in one list:** Metaphor renamed Exa (Jan 2024); `/research` endpoint retired (Apr 2026); `livecrawl` replaced by `maxAgeHours`; `linkedin` category replaced by `people`; `research paper` category replaced by `publication`; `pdf`/`github`/`tweet` categories deprecated; `use_autoprompt`, `resolvedSearchType`, `highlightScores` removed; crawl-date filters ignored. **Websets** (the high-compute list-building product Exa called one of its only two products in Sept 2025) is now in maintenance mode: its docs tell new users to use Exa Agent instead and keep Websets for existing integrations.

**Current list prices** (exa.ai/docs/admin/pricing): Search `instant` $4 per 1,000 requests; `fast`/`auto` $7 per 1,000 (10 results with text and highlights included); extra results $1 per 1,000; AI summaries $1 per 1,000 pages; Deep $12 and Deep-reasoning $15 per 1,000; Contents $1 per 1,000 pages per content type; Answer $5 per 1,000; Monitors $15 per 1,000; Agent $0.012 to $1.00 per fixed-effort run, or metered ($0.10 per compute unit plus $0.005 per search, $5 default cap on `auto`, $20 on `ultra`). Free tier: $10 of credits every month plus a one-time $10 bonus. Enterprise: up to 1,000 results per search, custom rate limits, custom indexes, SLAs and MSAs, ZDR, volume discounts, postpaid invoicing.

## 3. The Forward Deployed Engineer role

**What the NYC posting says** (jobs.ashbyhq.com/exa/c542d672-691c-46c1-9741-856d66f2c2ea, published Aug 13, 2026, in-person NYC, $130K to $275K plus equity and bonus, GTM department)
- FDEs sit between product, engineering and customer success, embed with customer engineering teams, and own a customer from first cold outreach through production integration to a closed deal. The posting's own summary: "an engineer who sells and a seller who ships."
- Day-to-day duties listed: build demos, tutorials and sample apps; debug anything from API behavior to frontend rendering; spot patterns in customer feedback and ship fixes yourself; run many sales and technical calls a week, pitching differently to CTOs, engineers and PMs; watch usage data for churn risk and expansion.
- Requirements: several years of programming (could stand up a production server), high performance in a demanding setting, comfort in high-stakes customer conversations, tolerance for context switching, travel.

**Sibling postings give a sharper spec** (FDE EMEA and FDE APJ, same team, newer template)
- The FDE is paired with an Account Executive and owns the "technical win": discovery with the customer's engineers, solution design on Exa's API, demos, POCs/POVs (proof of concept or proof of value, a time-boxed trial with agreed success criteria), and technical objection handling.
- They expect you to scope a POC with clear success criteria, run evaluations rigorously, answer hard questions honestly and admit when you need to find out, handle security questionnaires and RFPs, and build reusable demos and playbooks.
- They say AI-assisted coding is expected and hand-crafted code is not the bar.

**How Exa grades demos internally** (Technical Enablement Manager posting): the enablement function exists to raise the bar on demo excellence and the POV/POC process for FDEs, turn launches into value-based narratives, technical objection handling and competitive positioning, and build demo scenarios across industries and personas.

**What a good FDE at Exa does day to day** (my synthesis of the postings above): mornings in a customer's code or a Slack channel fixing an integration (search type choice, filters, highlights size, latency, rate limits); afternoons on discovery and demo calls with an AE; building a tailored prototype for each serious prospect; running side-by-side evals against the customer's current provider; filling security questionnaires; watching usage dashboards for accounts that are dropping or ready to expand; feeding repeated asks back to product.

**What the Oct 2 demo round is probably testing** (inference from the recruiter brief plus the postings, not stated by Exa):
1. Discovery framing: a specific enterprise buyer, a named end user, the workflow before and after, and a measurable pain (hours, cost, missed signals). The brief explicitly asks you to make clear who the end user is.
2. Product judgment: picking the right Exa primitive (Instant vs Auto vs Deep search, `category` filters, highlights, Contents, Monitors, Agent, Connect) and being able to say why not Google grounding, Perplexity or Tavily.
3. Technical build: a working applet on real external content, shown live, that survives an unexpected query.
4. Narration: the same story told at CTO, engineer and PM altitude; the customer-story format Exa uses (problem, why Exa, integration, metric) is a good template.
5. Business impact and next step: a POC plan with success criteria, an eval set, a cost model, and an expansion path (more seats, more workflows, more queries).
6. Honesty under questioning: knowing where Exa is weaker (section 4) and saying so.

Alignment note: finance is a market Exa is visibly investing in (Financial Markets data category, Snapshot for backtesting, Connect partners Financial Datasets, Macrobond and Baselayer KYB, Agent Ultra use cases naming market mapping, KYC and portfolio monitoring). GTM enrichment is Exa's most documented enterprise story (HubSpot, monday.com, 11x, GTM Intelligence demo).

## 4. Competitors: where Exa wins and loses

Caveat that applies to every row: Exa's numbers come from Exa-run benchmarks (open-sourced at github.com/exa-labs/benchmarks, so re-runnable), and competitors publish benchmarks where they win. The only independent comparison I found is AIMultiple (published May 25, 2026, updated Sep 27, 2026; 100 queries, 5 results each, GPT-5.2 judge): Brave 14.89, Firecrawl 14.58, Exa 14.39, Parallel Pro 14.21, Tavily 13.67, Parallel Base 13.50, Perplexity 12.96, SerpAPI 12.28. The top four overlap within error bars; Exa scored highest quality on technical documentation queries. AIMultiple discloses that SerpApi subscribes to its benchmarking service.

**Tavily** (acquired by Nebius, announced Feb 10, 2026; $275M upfront, up to $400M, per SiliconANGLE citing Calcalist; 1M+ developers per Nebius; customers include IBM, Cohere, Groq, MongoDB, monday.com, LangChain, AWS)
- Exa wins: dedicated people, company and paper indexes (Exa's Aug 2026 run: people rank-1 recall 75.5% vs 40.5%); tighter tail latency (Exa-measured p99 437ms vs 576ms); larger domain allow/block lists (1,200 vs 300/150); independence (no parent company steering the roadmap).
- Exa loses: Tavily bundles raw page content into a simple credit price ($0.008 per credit, basic search 1 credit, advanced 2) and publishes a higher standard rate limit (1,000 requests/minute); Nebius customers get one-vendor consolidation; big developer footprint. Note monday.com appears as a customer of both, so big buyers multi-source.

**Perplexity Sonar / Search API / Agent API** (Search API launched Sep 26, 2025 at $5 per 1,000; Fast Search $1 per 1,000; Agent API web search tool $2.50 per 1,000 invocations, plus `people_search` and `finance_search` tools at $5 per 1,000; claims an index of hundreds of billions of pages; now ships an MCP server)
- Exa wins: the developer controls retrieval (filters, categories, 1,200-domain lists, query-specific highlights, full page text) rather than getting a synthesized answer; Exa reports 64.8% vs 60.1% on a 500-query eval it attributes to Thinking Machines (Exa-reported, not verified); Exa ahead in AIMultiple.
- Exa loses: Perplexity's fast tier is cheaper than Exa Instant ($1 vs $4 per 1,000); one-call cited answers; consumer brand. Parallel's Sep 2026 BrowseComp chart shows Perplexity 74% vs Exa Auto 70% at lower cost (Parallel-reported). Warning: Exa's Perplexity comparison page (last updated Feb 6, 2026) says Perplexity has no MCP server and no people search; Perplexity's docs now show both, so do not repeat those claims.

**Brave Search API** (independent index, 30B+ pages per Brave's API page, 40B in a later Brave article; Search $5 per 1,000, Answers $4 per 1,000 plus $5 per million tokens; 50 queries/second; ZDR; customers AWS, Shopify, Snowflake, Cohere, Mistral, Chegg)
- Exa wins: entity retrieval (Exa's run: people rank-1 72% vs 44.4%); latency (Exa-measured p50 235ms vs 502ms); query-selected highlights.
- Exa loses: cheaper list price; Exa's own table concedes Brave's better citation precision (0.328 vs 0.259); Brave ranked first and fastest (669ms) in the independent AIMultiple test. Brave's own May 2026 article argues Exa's semantic matching can return conceptually similar but irrelevant pages and misses the long tail (its claim that Exa returns only URLs and snippets is out of date, since Exa returns full text and highlights by default).

**Parallel Web Systems** (Parag Agrawal; $100M Series A at $740M, then $100M Series B at $2B led by Sequoia on Apr 29, 2026; $230M total; 100,000+ developers; customers Clay, Harvey, Notion, Opendoor and others; products Search, Extract, Responses, Task, FindAll, Monitor, Chat; claims its own web-scale index; SOC 2 Type II, HIPAA-ready, ZDR; from $1 per 1,000 requests)
- Exa wins (Exa-reported, July 2026): faster and more accurate at matched latency budgets on public multi-hop datasets (FRAMES 0.46 vs 0.295, SealQA 0.270 vs 0.135); people and company search inside one endpoint; Exa Agent High at $0.50 scoring 74% on BrowseComp vs Parallel Ultra8x 58% at $2.40.
- Exa loses: Parallel's own Sep 9, 2026 BrowseComp chart shows the reverse (Parallel 74% at $399 per 1,000 questions vs Exa Auto 70% at $971, calling Exa the most expensive frontier run); Exa concedes Parallel has a higher compute ceiling per task and better extraction of hard PDFs and JavaScript pages; Google made Parallel a native grounding provider on July 16, 2026 with billing through the Google Cloud Marketplace invoice, which is easier procurement than Exa's bring-your-own-key setup. This is Exa's closest, equally funded peer.

**Linkup** (Paris; $10M seed led by Gradient, early 2026; offices NY, SF, Paris; logos include KPMG, McKinsey, EY, Databricks, Cohere; SOC 2 Type II, HIPAA, ZDR; private index and bring-your-own-cloud deployment; claims state of the art on Verified SimpleQA)
- Exa wins: scale of index, funding and product breadth (entity indexes, Agent, Connect, Monitors).
- Exa loses: Linkup offers private-index and in-customer-cloud deployment, which appeals to regulated European buyers, and it markets migration away from Exa on accuracy and cost (Linkup's claim).

**Firecrawl** (crawl, scrape, extract; $75M Series B led by Smash Ventures, Sep 22, 2026; new "Alexandria" knowledge base with 82 data providers)
- Exa wins: finding the right pages across the open web (discovery) and returning only relevant passages; Exa's run: company rank-1 81.5% vs 61.7%, papers 63.3% vs 26.3%.
- Exa loses: full-page extraction and whole-site crawling and mapping, which Exa's own page concedes; second place in AIMultiple with the highest mean relevance.

**Google grounding** (Grounding with Google Search in Gemini: $14 per 1,000 grounding queries on Gemini 3 with 5,000 free per month, billing began Jan 5, 2026; older models $35 per 1,000 prompts; Web Grounding for Enterprise $45 per 1,000 prompts on older models; Gemini only; the model decides what to search. Google's Custom Search JSON API is closed to new customers and ends Jan 1, 2027.)
- Exa wins: works with any model, the developer writes the query and filters, raw results and full text, entity categories.
- Exa loses: Google's index and brand, and one-toggle convenience for Gemini shops. Nuance: Google is also a channel for Exa (Grounding with Exa, Agent Marketplace), and it now offers Parallel the same way.

**Bing** (Bing Search APIs retired Aug 11, 2025; replacement is Grounding with Bing Search in Azure AI Foundry at $14 per 1,000 transactions, returning model output with citations; Microsoft restricts use of the output to its own products)
- Exa wins: any cloud, any model, raw results usable anywhere.
- Exa loses: Azure-standardized enterprises can use existing Microsoft contracts.

**You.com API** (Series C $100M at $1.5B, Sep 3, 2025, led by Cox; 1B+ API queries per month; customers DuckDuckGo, Windsurf, Harvey; Search $5 per 1,000, Contents $1 per 1,000 pages, Research $12 per 1,000 per Exa's reading of You.com pricing; Finance Research API with licensed S&P Global data)
- Exa wins: entity categories, re-runnable published benchmarks, query-dependent highlights; Exa reports You.com errored on 95 of 200 SimpleQA queries (competitor-reported).
- Exa loses: cheaper raw search; a dedicated finance research endpoint with licensed data, directly relevant to a financial-services pitch.

**SerpAPI-style scrapers (SerpAPI, Serper)** (return Google's results page as JSON; SerpAPI entry plan $25 per month for 1,000 searches per Exa's Aug 2026 reading)
- Exa wins: returns content not links, so no extra fetch-and-clean steps; no dependency on Google's ranking or terms; lower per-call price; no legal cloud. Google sued SerpApi on Dec 19, 2025 under the DMCA; per a third-party summary, a judge dismissed the core claims on July 20, 2026, Google refiled Aug 10, and a second motion to dismiss is pending.
- Exa loses: anything that needs what Google actually shows (rank tracking, SEO, shopping and local packs). SerpApi's March 2026 post argues Exa's index can be stale while a live SERP is current; it concedes Exa is faster.

## 5. Enterprise objections and the best honest answer

1. **Freshness ("your index is stale").** Honest answer: Exa is an index, and refresh timing varies by source (Exa's own FAQ says so). Controls: `maxAgeHours` on contents (0 forces a live crawl, -1 cache only, N re-crawls if older than N hours), news category and published-date filters, Monitors for scheduled change detection with webhooks, Snapshot to reproduce what a page said on a past date. For live numbers like prices, use the financial data category or a Connect partner rather than a scraped article. Live crawls cost latency and can fail on blocked sites. Also admit that in April 2026 the crawl-date filters started being ignored silently, which a third-party blog flagged as a stale-data risk; the mitigation is the changelog plus `maxAgeHours` and published-date filters.
2. **Coverage ("will you have my sources?").** Honest answer: 1.4T URLs tracked and 100B pages served (Aug 2026), but ExaSearchBot respects robots.txt and does not get past logins, paywalls or CAPTCHAs, so premium paywalled content is absent unless it comes through an Exa Connect partner or a custom index on an enterprise plan. Brave argues Exa misses the long tail. Best move: offer a side-by-side on the customer's own 50 to 100 real queries and measure it, which is exactly the demo offer on Exa's enterprise page.
3. **Hallucinated citations downstream.** Honest answer: Exa's FAQ itself says retrieval reduces unsupported claims but the application and its LLM remain responsible. What Exa gives: source URLs plus the exact text used, highlights that cut irrelevant context, and Deep search structured outputs with per-field citations and confidence. Recommend a citation check in the app (does the cited passage actually contain the claim) and an eval set. Never promise zero hallucinations.
4. **Data retention and security.** SOC 2 Type II with reports and DPA in the Trust Center; GDPR and CCPA; Zero Data Retention on Enterprise plans, enabled per team, for Search, Contents and Agent but not Answer or Websets; ZDR Agent runs cannot use Connect data sources; HIPAA mode with a BAA only for cached retrieval (Instant or Fast search, no summaries, no live crawl). The default retention for non-ZDR accounts is not stated on the pages I read, so say you will find out. ZDR is table stakes now (Brave, Parallel, Linkup and You.com all offer it), so do not pitch it as unique.
5. **Cost at scale.** Honest answer: Exa is not the cheapest per call (Perplexity Fast $1, Parallel from $1, Brave and Perplexity Search $5, Exa $4 to $7 per 1,000), but Exa's price includes page contents for 10 results. Frame total cost as search fee plus downstream LLM tokens plus engineering time; Exa claims up to 94% fewer tokens with highlights and about 49% better token efficiency with Dynamic Highlights (research preview). Enterprise gets volume discounts, committed-use plans and invoicing; Agent runs have hard dollar caps. Expect Parallel's claim that Exa is expensive at the frontier; answer with cost per correct answer on the customer's own task and the right search type for each step.
6. **Build versus buy.** Honest answer: building a web-scale index took Exa years, a GPU cluster and trillions of tracked URLs; the traditional "rent Google or Bing" options are closing (Bing API retired Aug 2025, Bing grounding output restricted to Microsoft products, Google Custom Search API ends Jan 1, 2027), and scraping Google carries legal risk (Google v. SerpApi). But if the customer only needs a fixed list of known sites, crawling those directly (or Firecrawl) may be cheaper; Exa earns its price on discovery across the open web and entity search.
7. **Vendor and API stability (a likely follow-up).** Exa shipped a breaking SDK change in Oct 2025 and deprecations in April 2026. Answer: enterprise MSAs and SLAs, a public changelog, pin SDK versions, and a well-funded independent vendor ($250M Series C) versus Tavily's new parent company.
8. **"Why not the model's built-in web search?"** HubSpot's case study says Exa beat the native model search experience for them, and Exa's demo gallery includes an "Exa vs Native Search" side-by-side.

## 6. What is public about how Exa runs demos and POCs

- Enterprise page: "Book a demo" asks the prospect to bring a query their current search gets wrong, and Exa runs it live on the call. The same page lists forward-deployed engineers working with the customer on integration, evals and retrieval quality, plus custom indexes, capacity controls, committed-use pricing and SLAs.
- FDE EMEA/APJ postings: FDE and AE pair up; discovery, solution design, tailored demos and prototypes, POCs/POVs with defined success criteria, security questionnaires and RFPs, reusable demos and playbooks.
- Forward Deployed PM posting: tailored solutions and proof-of-value demos, and helping price custom engagements.
- VP Customer Experience posting: onboarding with clear milestones and a sales-to-post-sales handoff, usage-based health scores, NDR as the key metric.
- Self-serve trial path: $10 free credits per month, dashboard playground, free MCP tier, open benchmark repo that buyers can re-run, and "switching from X to Exa" parameter-mapping guides on each comparison page.
- Demo gallery (exa.ai/demos): Exa vs Native Search, Company Enrichment, GTM Intelligence (one domain in, cited TAM list, scored prospects, decision makers, then Monitors for alerts), Web-Grounded Chat, Voice Agent, People Enrichment, Paper Search, Product Shopping, Exa Terminal, Subject Image Search.
- Customer-story format with hard numbers you can mirror on slides: monday.com (2.7M enrichments, 50% less research time per rep, top 10 leads waiting in CRM at login); CodeRabbit (P50 latency 7.1s vs 30 to 45s before, 70 to 75% fewer search calls); HubSpot (40% latency improvement, millions of company searches, uses Search and Monitors).

## 7. Inconsistencies to avoid repeating in the interview

- Exa comparison pages dated Feb and Mar 2026 still quote Exa at $5 per 1,000; current pricing is $4 (Instant) and $7 (Fast/Auto).
- Exa Instant latency appears as sub-150ms (changelog), 178ms p50 (enterprise page), 235ms p50 (comparison pages), 323ms (search page chart). Say "a few hundred milliseconds or less, depending on how it is measured."
- Index size: 500B+ pages (about page, May 2026 coverage) vs 1.4T URLs tracked and 100B served (Aug 2026 FAQ).
- Developers: 400,000 (May 2026) vs 500,000 (enterprise page now). Headcount: about 100 vs about 150.
- Sacra lists Exa's founding year as 2011; Exa's own Series B post says 2021.

## Pages that would not load or had no usable content
- bloomberg.com Series C article (403). perplexity.ai/api-platform (403; used docs.perplexity.ai pricing instead). jobs.ashbyhq.com/exa renders client-side and showed no jobs; I used Ashby's public posting API for the same board. The a16z Bryk podcast page and the Yahoo Finance Bryk video page had no transcript. exa.ai/security is only a vulnerability disclosure policy; I did not read trust.exa.ai. Google Cloud pricing page was truncated in WebFetch; I read it by direct download.
