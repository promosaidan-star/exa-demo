## Exa demos, customers and verticals (researched 2026-09-29)

### Summary
- **What Exa already shows a lot:** Exa's public demos and customer stories mostly cover three things:
  1. Sales prospecting data, which Exa calls GTM (go-to-market).
  2. Grounding chatbots and agents in the live web.
  3. Search over research papers.
  An applet in any of these three will look like it was copied from Exa's own gallery.
- **Finance is Exa's next push.** The evidence:
  - The main comparison demo uses finance and regulation examples.
  - The enterprise page has a Finance section.
  - Exa Connect, Exa's marketplace of third-party data sources, lists finance data providers.
  - Exa Snapshot, a new feature that searches the web as it looked on a past date, is pitched at quant backtesting. A live webinar on it is on **Thu Oct 1, 1 PM ET**, the day before AJ's demo.
  - Exa's own GitHub has a stock-sentiment demo built for a bank.
- **What is missing in finance:** Almost all of it is about stocks or private markets. I found **no** public demo for fixed income, buy-side operations, trading-technology vendors, wealth management or energy markets.
- **No finance customer is named.** The live /customers page has none. The three finance stories that did exist (a private equity firm, an investment bank and a consultancy) had no company names and now return 404. I read them through the Wayback Machine.
- **Context for the interview:** The NYC Forward Deployed Engineer (FDE) job post lists building and shipping demos, tutorials and sample apps as part of the job (https://jobs.ashbyhq.com/exa/c542d672-691c-46c1-9741-856d66f2c2ea). The enterprise page also sells FDEs as a service: customers work directly with Exa engineers on integration, evals and retrieval quality (https://exa.ai/enterprise).

A copy of every page I read is saved in: `C:\Users\ajwal\AppData\Local\Temp\claude\C--Users-ajwal\de92077b-64e0-4838-979e-5add8ad34faf\scratchpad\exa`

---

### 1. Every public Exa demo

**Where the demos live**
- https://exa.ai/demos lists 10 demos.
- The navigation bar inside https://demos.exa.ai shows **19**, grouped as Assist, Build & Evaluate, Discover, Enrich, Monitor and Research.
- The demos.exa.ai home page opens by asking what you are building, and its first starter option is enriching a list of leads.
- **None of the demos.exa.ai pages link to source code.** In the source column below, "likely" means an exa-labs GitHub repo whose name or page routes match. The demo page itself does not link to it.
- Where I inferred the target user, it is marked "(inferred)".

| # | Demo | URL | Target user | Exa capability shown | Source public? |
|---|---|---|---|---|---|
| 1 | Exa vs Native Search | https://demos.exa.ai/exa-vs-native-search | AI engineers choosing between their LLM provider's built-in search and Exa | Search with highlights (short excerpts pulled from each page) vs provider-hosted search. The preset prompts are all finance or regulation: largest US bank holding companies from the Fed NIC table, UK FCA Consumer Duty, Nvidia earnings brief, BLS CPI print, EU AI Act | No link found |
| 2 | Token Savings (not on exa.ai/demos) | https://demos.exa.ai/tokencalculator | Engineering leads watching LLM costs (inferred) | Highlights cutting input tokens. It covers 8 verticals: academic, coding, ecommerce, finance, legal, medical, news, travel. Default view: 77.0% fewer tokens, 61.9% lower cost, accuracy 94.2% for Exa vs 91.2% native, on 960 matched questions graded by Gemini | No |
| 3 | Web-Grounded Chat | https://demos.exa.ai/chatbot-demo | Chat app builders | Search plus an LLM answering with citations (RAG, meaning the model answers from retrieved pages). Presets include "which YC-backed autonomous vehicle startups raised this month" | Likely https://github.com/exa-labs/chatbot-demo |
| 4 | Web-Grounded Voice Agent | https://demos.exa.ai/voice | Voice assistant builders | Low-latency search inside a voice loop | No |
| 5 | Exa Terminal / Search Terminal | https://demos.exa.ai/exa-terminal | Coding-agent developers | Exa tools served over MCP (Model Context Protocol, a standard way to plug tools into AI agents), running on Gemini 3.7 Flash | Demo no. The MCP server is public: https://github.com/exa-labs/exa-mcp-server |
| 6 | Grounding Comparison (not on exa.ai/demos) | https://demos.exa.ai/gemini-exa-grounding | Gemini and Google Cloud developers | Grounding with Exa on Gemini, used to build product catalogs (Japanese whisky, gin and sake with JAN barcodes, price, ABV) | No |
| 7 | Content Retrieval (not on exa.ai/demos) | https://demos.exa.ai/content-retrieval | Developers | Contents API, comparing hits from Exa's stored index with live crawling for news, shopping and reference URLs | No |
| 8 | Product Shopping | https://demos.exa.ai/shopping-demo | Consumers and e-commerce apps | Natural-language product discovery | No |
| 9 | Subject Image Search | https://demos.exa.ai/image-search-demo | Media and brand teams (inferred) | Search plus image results, filtered with regex or gpt-5.4-nano | No |
| 10 | Candidate Sourcing (not on exa.ai/demos) | https://demos.exa.ai/candidate-sourcing | Recruiters | Agent API runs that verify each candidate against hard requirements, dedupe against an uploaded list and exclude current employees | No |
| 11 | Network Planning (not on exa.ai/demos) | https://demos.exa.ai/network-intel | Infrastructure or telecom planners (inferred) | Deep searches over construction notices, permits, new developments and local infrastructure signals, for expansion and capacity planning | No |
| 12 | People Enrichment | https://demos.exa.ai/people-enrichment | Sales and recruiting | Deep search returning structured fields about a person | No |
| 13 | Company Enrichment | https://demos.exa.ai/enrichment-demo/visualization | Sales and RevOps | Filling in company records | Likely https://github.com/exa-labs/company-enrichment-demo (Answer API, same /visualization route) |
| 14 | GTM Intelligence | https://demos.exa.ai/gtm-intelligence | Sales and RevOps | Five steps: deep search with a schema builds an ideal-customer profile from a domain; parallel deep searches build the prospect list; each prospect is enriched and scored with citations; people search finds decision makers; Monitors re-run the enrichment on a schedule | No (a code snippet is shown on the page) |
| 15 | Adverse Media (not on exa.ai/demos) | https://demos.exa.ai/adverse-media-screen | Compliance and KYC (know-your-customer) analysts | One deep search per risk topic across 8 topics: fraud, money laundering, sanctions, bribery, litigation, regulatory action, data breach, environmental. Examples: Wirecard, FTX, Boeing, Wells Fargo. Carries a disclaimer that it is not a compliance determination | No |
| 16 | Market Monitor (not on exa.ai/demos) | https://demos.exa.ai/market-monitor | Investors and competitive-intelligence teams (inferred) | A watchlist of 10 AI companies (leadership, headcount, funding, valuation) with event streams and a time scrubber. That it runs on the Monitors API is my inference | No |
| 17 | Morning Briefs (not on exa.ai/demos) | https://demos.exa.ai/morning-briefs | Executives | Daily brief of company signals, competitor news and industry news, retrieved from Exa's index, filtered for freshness and deduplicated. The example is synthetic (a home-services firm) | No |
| 18 | Paper Search | https://demos.exa.ai/paper-search | ML researchers | Research-paper category with time filters and researcher lookup | Older version: https://github.com/exa-labs/research-paper-app |
| 19 | Research Map (not on exa.ai/demos) | https://demos.exa.ai/research-map-demo | Scientists (oncology, gene therapy, neuroscience presets) | Exa finds papers and Claude maps how they connect as a graph | No |

**Older or open-source demos in https://github.com/exa-labs** (the Nov 2025 demos page is from Wayback snapshot 20251103204127):
- company-researcher: 1,506 stars, live at https://company-researcher-exa.vercel.app
- exa-hallucination-detector: still live at https://demos.exa.ai/hallucination-detector
- exa-writing-assist
- answer-chat-app
- websets-news-monitor
- exa-deepseek-chat, gpt-oss-exa-chat and exa-o3mini-chat (the last one archived)
- research-paper-app
- startup-idea-validator
- substack-exa-search
- opus-v-oai: engineer sentiment about AI models
- jfk-files-app (archived)
- roast-my-website
- **Demos/mizuho-applet.** This is the most relevant to AJ. It lives at https://github.com/exa-labs/Demos/tree/HEAD/mizuho-applet.
  - It was committed on 2026-01-22 by an Exa employee working with Devin.
  - Its spec file calls it a stock sentiment analyzer bank demo.
  - It compares bull and bear points from professional finance sites with Reddit investing communities for a ticker, and adds a price chart, news-volume momentum and a key-events timeline.
  - It lets you pick exchanges including Tokyo, London and Hong Kong.
  - The folder name does not prove Mizuho is a customer.

**Tutorials on the Nov 2025 demos page:** news summarizer, Hacker News clone, recruiting agent.

**Retired demo:** Clinical Trial Monitor was on the demos page in March 2026 (Wayback 20260330192158). It now redirects to the demos.exa.ai home page.

---

### 2. Customer stories and case studies

**A. Live on https://exa.ai/customers.** All 13 are linked from that page. Fireworks is only in the sitemap.

| Customer | Industry | What they use Exa for | Numbers quoted | URL |
|---|---|---|---|---|
| Firefox (Mozilla) | Web browser | AI answers with citations: Smart Window on desktop and Quick Answers on iOS. Exa's zero data retention was required | Exa index of 1.4 trillion URLs and 100 billion documents | https://exa.ai/customers/firefox |
| monday.com | CRM / Work OS | Agentic lead engine: plain-English ICP (ideal customer profile) in, structured cited leads out. Also used internally for recruiting | 2.7M enrichments; 50% less research time per SDR/AE (sales development rep / account executive); top 10 leads per rep per day; 250,000+ customers | https://exa.ai/customers/monday |
| HubSpot | CRM | People and company search for Breeze Assistant and Agents; Monitors API for web change events. Previously used a model's built-in search | 40% better latency; millions of company searches; real-time news monitoring | https://exa.ai/customers/hubspot |
| Cognition | AI engineering | Powers web search across Devin | None | https://exa.ai/customers/cognition |
| CodeRabbit | Developer tools | Checks AI code-review comments against current docs, changelogs and packages using Deep Search | 70-75% fewer search calls; P50 7.1s and P95 11.1s, down from 30-45s with the old provider; 7-10% of PRs trigger a check | https://exa.ai/customers/coderabbit |
| OpenRouter | AI infrastructure | Search tool shared across all models through openrouter:web_search | 73M queries to date, up from 2.36M+ the year before; 400+ models | https://exa.ai/customers/openrouter |
| 11x | AI sales automation | Finding unusual prospect signals beyond funding and hiring; Websets | 7.2M+ searches; 2.7M+ Webset items; 67K+ enrichment cells | https://exa.ai/customers/11x |
| HockeyStack | Revenue intelligence | People search inside revenue agents | 9.1M+ searches; compared 5 providers; 1B+ profiles refreshed weekly | https://exa.ai/customers/hockeystack |
| Anara | Scientific research | Paper discovery and accurate citations for scientists | None | https://exa.ai/customers/anara |
| WebFX | Digital marketing | Content and competitor research, grounding internal chat, sales enrichment, LLM SEO next | Under 450 ms latency; 500+ staff | https://exa.ai/customers/webfx |
| WhyHow.AI | Legal tech | Spotting early class-action and mass-tort signals for plaintiff firms | 30% more accurate sources; case detection "years" earlier; millions of pages a day; a $40B industry | https://exa.ai/customers/whyhow |
| StackAI | Enterprise AI agent platform | Exa is a drag-and-drop node and also the default web search in its agent builder. Its customers use it for due diligence, competitive intelligence, RFP drafting and market research | 2 weeks from integration to deployment; 10x research capability; 24/7 | https://exa.ai/customers/stackai |
| Obvious | Data infrastructure | Websets for lookalike company lists and finding contacts | 20x faster research iterations; 99% cost cut; one call replaces 15-20+ manual iterations; "hundreds of thousands" of dollars replaced by "a few dollars" | https://exa.ai/customers/obvious |
| Fireworks (sitemap only) | AI infrastructure | Colab tutorial for a paper-research assistant | None | https://exa.ai/customers/fireworks |

**Other named customers with no story:**
- Enterprise page logos: Cursor, Databricks, AWS, Klarna, Groq (https://exa.ai/enterprise).
- Homepage logos: Browserbase and Legora (https://exa.ai). Legora is a legal AI workspace (https://legora.com).
- The partners page quotes Databricks' chief AI scientist saying Exa found training data they could not get another way (https://exa.ai/partners).

**B. Anonymous case studies that now return 404.** I read these through Wayback Machine snapshots.

| Case study | Industry | Use | Numbers | Archive |
|---|---|---|---|---|
| Private equity | PE, $500B+ AUM | Internal research co-pilot with zero data retention, plus Websets monitoring of 200+ portfolio companies | Over 30% less analyst and associate research time | https://web.archive.org/web/20260510024438/https://exa.ai/blog/private-equity-case-study |
| Investment banking | Top-10 M&A advisory bank by deal volume | Finding LPs (limited partners, the investors in funds), tracking GP (general partner) fundraising, enriching the CRM (Websets and research endpoint) | 3x more qualified LP prospects | https://web.archive.org/web/20260422200757/https://exa.ai/blog/investment-banking-case-study |
| Consulting | Global consultancy, 30,000+ staff | Strategy co-pilot grounded in live web data | Research was up to 20% of project time; now 30-50% less time spent on it | https://web.archive.org/web/20260209184928/https://exa.ai/blog/consulting-case-study |
| CRM platform | CRM software | Websets lead enrichment, news alerts, lookalike discovery | Qualitative only | https://web.archive.org/web/20260314173625/https://exa.ai/blog/crm-platform-case-study |
| Search engine | Consumer search | Answer endpoint summaries shown above results | Rolled out from 10% to 50%+ of users; 70%+ positive sentiment | https://web.archive.org/web/20260422203432/https://exa.ai/blog/search-engine-case-study |
| AI writing assistant | Education and writing | Live citation engine | $6M ARR growth; 10% free-to-paid conversion lift; 230+ schools | https://web.archive.org/web/20260124055302/https://exa.ai/blog/ai-writing-assistant-case-study |
| Notion | Productivity | Web search in Research Mode, with privacy as a requirement | Millions of queries a month | https://web.archive.org/web/20260401012514/https://exa.ai/blog/notion-exa |
| Flatfile | Data infrastructure | Same text and CEO quote now shown under Obvious | Same as Obvious | https://web.archive.org/web/20260107223300/https://exa.ai/blog/flatfile-exa |

The legal-tech case study URL now redirects to /customers/whyhow.

---

### 3. Enterprise verticals Exa is pushing, strongest first

1. **GTM and sales intelligence (by far the strongest).**
   - It is the only dedicated use-case page, with a pricing calculator and a live signal feed (https://exa.ai/use-cases/gtm).
   - 3 of the 10 listed demos are GTM, and the demos.exa.ai home page's first starter option is enriching a list of leads.
   - Customers: monday, HubSpot, 11x, HockeyStack, Obvious.
   - The Series C post lists GTM agents first among why customers choose Exa (https://exa.ai/blog/announcing-series-c).
   - Exa Connect partners here: ZoomInfo, Crunchbase, Harmonic, Fiber.ai (https://exa.ai/connect).
   - Most Agent API examples are GTM (https://exa.ai/docs/agent/examples.md).
2. **Coding agents.**
   - Cognition, CodeRabbit and Cursor.
   - Software engineering is the first section on the enterprise page.
   - The Series C post says Exa is used by nearly every coding agent.
3. **AI platforms and grounding for consumer AI products.** OpenRouter, StackAI, Firefox, Notion (archived), the search-engine case (archived), Google Cloud Gemini grounding (https://exa.ai/blog/exa-google-cloud).
4. **Financial services (rising fast).**
   - The enterprise page Finance section lists SEC filings, earnings calls, company websites and financial news.
   - The Financial Markets docs page lists equity and credit research, KYC/KYB/adverse-media screening, portfolio and policy monitoring, and deal sourcing (https://exa.ai/docs/search/data/financial.md).
   - The Agent Ultra post has a "Financial services" section: diligence market maps, KYC research and portfolio signal monitoring (https://exa.ai/blog/exa-agent-ultra).
   - The Exa Agent launch post names finance agents (https://exa.ai/blog/exa-agent). The Agent page reports the FinanceAgent-V2 benchmark (https://exa.ai/products/agent).
   - Snapshot is pitched for quant backtesting (https://exa.ai/blog/exa-snapshot). The Oct 1 webinar targets quant, forecasting and fintech teams (https://exa.ai/webinars/exa-snapshot-live).
   - Exa Connect finance partners:
     - Self-serve: Financial Datasets, Macrobond, Polymarket, Baselayer.
     - On request: Crunchbase.
     - DataBento and Alpha Vantage appear only as logos.
     - Sources: https://exa.ai/connect and https://exa.ai/docs/llms.txt
   - The flagship comparison demo uses finance and regulatory presets, and there are Adverse Media and Market Monitor demos.
   - The mizuho-applet repo.
   - The zero-data-retention post says many customers who moved from Bing's API shutdown were Fortune 500s and financial firms (https://exa.ai/blog/zdr-search-engine).
   - Weakness: no finance customer is named anywhere live.
5. **Private equity, VC and deal sourcing.** Archived PE and IB cases, Agent Ultra market maps, Crunchbase and Harmonic in Connect.
6. **Consulting.** Archived consulting case. Quantium is listed as a consulting and custom-deployment partner (https://exa.ai/integrations/quantium).
7. **Legal.**
   - WhyHow.AI, and the Legora logo.
   - Enterprise page Legal section.
   - Legal and Public Records docs page (https://exa.ai/docs/search/data/legal.md).
   - Agent Ultra's WANDR benchmark is modeled on due diligence and legal research tasks.
8. **Healthcare and life sciences.**
   - Enterprise page Healthcare and Scientific research sections, and a HIPAA agreement (BAA) is available.
   - DefinitiveHealthcare in Connect.
   - The Deep Search page samples use biotech and FDA approval examples (https://exa.ai/products/deep).
   - The Research Map demo and the retired Clinical Trial Monitor.
9. **Scientific research and academia.** Anara, Paper Search, the publications-search blog post, the archived writing-assistant case.
10. **Recruiting.** Candidate Sourcing demo, the old recruiting-agent tutorial, monday's internal use, Fiber.ai.
11. **Compliance, KYC and KYB** (KYB means know-your-business, the company version of KYC). Adverse Media demo, Baselayer, and KYB listed as an Agent use case.
12. **Smaller signals:** marketing (WebFX), commerce and travel (shopping demo, Affiliate.com, Jinko), cybersecurity docs page, infrastructure planning (Network Planning demo).

---

### 4. Use cases that are already overdone (avoid as the main idea)

- **Prospecting, lead or company enrichment and scoring.**
  - Demos: Company Enrichment, People Enrichment, GTM Intelligence.
  - Customers: monday, HubSpot, 11x, HockeyStack, Obvious, the CRM case.
  - The whole /use-cases/gtm page.
- **"Chat with the web" or answer engine.** Web-Grounded Chat, Voice, Exa vs Native Search, Token Savings, Grounding Comparison, plus five older chat apps on GitHub.
- **Company research brief.** company-researcher (the biggest repo, 1,506 stars), startup-idea-validator, and the Databricks brief in the Exa Agent post.
- **Research-paper discovery.** Paper Search, Research Map, the Fireworks tutorial, research-paper-app, Anara.
- **Stock sentiment, professional vs Reddit, for a bank.** Already built in mizuho-applet. Repeating it would look like a copy.
- **Plain news monitoring or morning briefs.** Websets News Monitor, Morning Briefs, Market Monitor, the PE portfolio-monitoring case.
- **Generic adverse-media or KYC screening.** Adverse Media demo, the KYB Agent example, Baselayer.
- **Candidate sourcing or recruiting.**
- **Code and docs search for coding agents.**
- **Hallucination checking or citation assistants.**
- **Private-market list building** (for example "every battery-recycling company in Europe") is already the Agent Ultra showcase.

---

### 5. Gaps: markets with an obvious need and no public Exa demo

The "what is missing" and "demo angle" columns are my analysis, not Exa claims.

| Market | What Exa shows today | What is missing | Demo angle AJ could own |
|---|---|---|---|
| Capital markets (sell side) | Equity sentiment (mizuho-applet), Nvidia earnings preset, archived IB LP-sourcing case | Market-structure and regulatory change for trading desks; exchange and venue notices | Desk-facing "what changed and what it breaks" feed with cited sources |
| Buy-side investment operations | Nothing. The PE case is front-office research, not operations | Corporate-action validation, counterparty and vendor due diligence for ops, custodian and broker notices | Ops analyst checks a corporate event against issuer releases, filings and exchange notices, with Snapshot as the audit trail |
| Fixed income and credit | The docs list "credit research" once. No demo or example. No bond, muni or covenant terms in the docs index I searched (https://exa.ai/docs/llms.txt) | Everything | Issuer credit-event monitor (rating actions, amendments, refinancings, distress news) for a credit analyst or PM |
| Trading technology vendors (OMS/EMS/FIX) | Nothing. The nearest pattern is CodeRabbit checking claims against changelogs and docs | Monitoring venue and broker spec changes, competitive intel for vendors | Onboarding and connectivity team radar for exchange technical notices and rule changes. This matches AJ's FIX background |
| Wealth management | Nothing. People and company enrichment are adjacent | Advisor prospecting on liquidity events, client life-event alerts | Advisor book scan for client and prospect events, with citations for compliance review |
| Energy markets | Nothing. Adjacent: Network Planning (permits and construction), Macrobond macro series | Power and gas market event monitoring | Trader or analyst feed of grid operator, regulator and outage news; Snapshot for point-in-time backtests |

**Two openings Exa itself has flagged**

1. **Exa has no finance research endpoint.** Exa's You.com comparison page admits You.com has a dedicated Finance Research endpoint with no Exa equivalent, and calls it a real differentiator for anyone building in that vertical (https://exa.ai/versus/you). A finance workflow built on Exa Agent, Search and Connect speaks directly to that gap.
2. **Snapshot has no demo yet.** Snapshot shipped Sep 17, 2026 as a research preview and does not appear among the 19 demos (https://exa.ai/blog/exa-snapshot). Two limits matter if AJ uses it:
   - Pay-as-you-go access covers only a rolling 5-month window, at 10 QPS (queries per second).
   - After 100 requests you have to talk to sales (https://exa.ai/docs/search/snapshot.md).

---

### 6. How Exa describes itself against plain web search and rivals

I used **one** direct quote because of a quoting limit I work under. Everything else below is a close paraphrase; the exact wording is at each URL.

- **The one direct quote**, from the Series C post (https://exa.ai/blog/announcing-series-c): "Most other search providers actually wrap other search engines."
- **Against Google and keyword search:**
  - Google's keyword matching fails on complex, multi-condition queries.
  - Websets returned over 20x more correct results than Google on Exa's own 200-query benchmark (https://exa.ai/blog/websets-evals).
  - Google and Bing have barely changed in a decade, and AI answer products sit on top of them (https://exa.ai/blog/perfect-search).
  - Exa has no ads and sells search only as an API (https://exa.ai/why).
- **Against Gemini + Google grounding:**
  - It calls Google grounding a black box: you cannot set queries, domains, dates or result counts.
  - Exa works with any LLM, returns 100+ results instead of about 10, and has people and company indexes (https://exa.ai/versus/google-search).
- **Against wrapper providers:**
  - Zero data retention needs your own independent index, because providers that scrape Google cannot offer it (https://exa.ai/blog/zdr-search-engine).
- **Against SerpAPI:**
  - SerpAPI measures Google's results page; Exa answers questions.
  - Price is $0.007 vs $0.025 per search (https://exa.ai/versus/serpapi).
- **Against Perplexity:**
  - It calls Perplexity's API a black box.
  - 64.8% vs 60.1% on a 500-query evaluation by Thinking Machines.
  - P95 latency 1.5s vs 5.1s (https://exa.ai/versus/perplexity).
- **Against Tavily** (acquired by Nebius, Feb 2026):
  - People search R@1 (right answer ranked first) 75.5% vs 40.5%.
  - Company search R@1 81.5% vs 61.3%.
  - Exa concedes Tavily fits teams that want full page text bundled in the price (https://exa.ai/versus/tavily).
- **Against Parallel:**
  - Exa leads FRAMES and SealQA at matched latency.
  - Agent High at $0.50 matches or beats Parallel's top tiers, including FinanceAgent-V2 at 64.2% vs 63%.
  - Exa concedes Parallel has a higher compute ceiling (https://exa.ai/versus/parallel).
- **Against Brave:**
  - Exa is built only for machine retrieval.
  - Exa concedes Brave leads on citation precision, 0.328 vs 0.259 (https://exa.ai/versus/brave).
- **Against Firecrawl:**
  - Firecrawl returns whole pages; Exa returns passages matched to the query.
  - Exa concedes Firecrawl is better for compliance review, contract analysis and archiving (https://exa.ai/versus/firecrawl).
- **Headline claims** (https://exa.ai/enterprise and https://exa.ai/products/search):
  - Highest quality at every latency.
  - Results in under 180 ms.
  - Up to 94% fewer tokens.
  - Zero data retention.
  - SOC 2 Type II.
  - HIPAA agreement available.
- **Demo framing tip:** Exa's own sales demo asks prospects to bring a query their current search gets wrong and runs it live (https://exa.ai/enterprise). That is a natural opening for AJ's walkthrough.