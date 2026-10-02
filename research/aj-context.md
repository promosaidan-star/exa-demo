# AJ's side of the Exa process: what was said, what is on file, where he has authority

Sources I read: the three Interview_Prep files, both Exa sections of APPLICATION_ESSAYS.md (lines 80 to 84 and 4939 to 4951), the twelve named memory notes plus aj_adroit_full_time.md and aj_adroit_title.md, both resumes Exa may hold, the Exa rows in application_log.csv, and these Gmail threads (read only): the call transcript 1a0d994cc377fa82, the thank-you to Sukhm 1a0d9d974b2c9a5e, Jenna's demo brief 1a0da9548e25e1f3, and the 10/2 reminder 1a0e9849b4690282. On the web I read exa.ai/blog, exa.ai/blog/exa-agent-ultra and exa.ai/docs/reference/search (docs.exa.ai/reference/search now redirects there).

The transcript comes from automatic transcription and is noisy. "forward department engineer" means forward deployed engineer, "Detroit" means Adroit, "Tetcher" means HedgeServ (the application log confirms this), "FTEs" almost certainly means FDEs, and "ex-Asian ultra" means Exa Agent Ultra. Below, "quoted" means quoted from the transcript as written.

---

## 1. What Sukhm Kang said on the 9/25 intro call

**Who he is.** He is an FDE (forward deployed engineer) at Exa, calling from the San Francisco office. He has been there "about like 2 months ish", and later agreed it was about three months. His last job was titled FDE, but he said it was "more of like infra engineer" with no part in sales. He called Exa "my 1st job where I'm involved in the sales process."

**What FDEs at Exa do, in his words**
- "a lot of context switching." He said Exa has "maybe around 5000" enterprise customers and "maybe 10 or 11" FDEs. He hedged both numbers, so treat them as rough.
- "always gonna be jumping on calls with customers and demoing Exa or working through issues."
- Competitive evaluations: FDEs make sure Exa shows its best "against other competitors". He added that this is "similar to what you mentioned on your resume". The Sales_Engineering resume opens with "Sales engineer who wins technical evaluations", so he had most likely read that resume.
- Pre-sales: "we're heavily involved in the pre-sales, especially in the technical evaluations", for example when a customer "is evaluating many vendors."
- After the sale: "implementation support", which means "looking at the customer's queries that they're putting into Exa and making sure that they're getting the most out of it."
- Many FDEs also run long projects "to make Exa better" alongside their customer work.
- Split with the AE (account executive, the salesperson): the AE handles "contracting" and manages the relationship. The FDE is "the main technical point of contact for the customer." He said the AEs are "super smart and organized" and ask FDEs for very clear things.
- Culture: the company is growing fast, has moved offices, and already feels "like a whole new company". His manager "takes an active interest" and gives him "interesting customers and interesting, like, long term projects."
- How he handles the load: using AI and agents (the transcript is unclear on who said this, but he agreed it is "a big part"), plus prioritizing: "not every issue is actually worth your time." On stress: "I wouldn't say that I feel stressed," and he suggested AJ ask "the next person who interviews you."

**Customers or verticals he named: none.** He gave no customer names and no industries. Nothing on the call tells AJ which market Exa wants to see.

**Interview process and demo round: nothing.** He left early for another interview and gave no next step. The demo brief came from Jenna Katlin at 6:00 PM ET the same day. It adds two points to what the orchestrator summarized. First, "walk through everything you'd plan to show to the customer, so we can see how you'd deliver each of the 3 steps." Second, "~30 minutes to walk us through your customer framing, the live Exa demo, and the business impact."

**How he reacted**
- He lit up when AJ mentioned the benchmark post: "Oh, is it the one from today... Because we just released one," and "a lot of people were working on that exact blog." That post is "Introducing Exa Agent Ultra - A New Frontier for Deep Research", dated September 25, 2026 (https://exa.ai/blog/exa-agent-ultra). Per that page it compares Exa against Opus 5.5, GPT-6 Astra (AJ said "GPT 6 extra") and Perplexity. It names finance use cases: "market mapping for due diligence, KYC compliance research", "company enrichment" and "portfolio monitoring". It also names "financial services" as a target. I read that page through a summarizing fetch tool, so re-read it before quoting any benchmark number.
- He was warm on hobbies ("very healthy and productive hobbies") and philosophy, and neutral-positive elsewhere ("Well, that makes sense", "Cool, yeah, that totally makes sense").
- **One friction point:** AJ told the Adroit story as what he built. Sukhm had to ask, "what was the context of why you needed to do this integration?" The lesson for the demo is to state the customer's problem first.
- Jenna afterwards: "Glad to hear the conversation with Sukhm went well!" She also confirmed sukhm@exa.ai.

## 2. What AJ has told Exa (keep the demo consistent with this)

**Two applications to the same posting.**
- 8/28, Forward_Deployed_AI resume. Why-Exa essay: "the hardest part was never the model; it was getting clean, timely, well-structured information into it. Retrieval quality was the bottleneck." It calls Exa "the rare AI company whose product gets more valuable the more agents exist". Two lines in it are wrong: "the last two years building an ML trading system", and "three years" at CRD. The other two essays were not saved word for word. The log summarizes them as proud-of = the ML trading system plus killing his own hypotheses with overlap-corrected t-stats (significance tests adjusted for overlapping time windows), and motivation = ownership and learning fast.
- 9/20, Sales_Engineering resume. The recruiter invite on 9/22 came from this one.
  - Why-Exa essay: onboarding buy-side clients at Adroit meant "living inside a client real data until it reconciled." He built a pre-go-live harness that listed every unmapped value instead of letting it silently default. Key lines: "Retrieval fails the same quiet way" and "I want to be the person in the room when that happens."
  - Proud-of: that same reconciliation harness.
  - Motivation: "Finding the failure nobody has noticed yet." He also cited trusting his null research results, and being the person customers can ask a hard technical question.
  - Earliest start: October 2026.

**Claims on the Sales_Engineering resume Exa holds.** These are on the page, so AJ must be able to back any he repeats:
- "Five years embedded with buyside trading firms and Fortune-500 clients".
- At Adroit: "10+ leading institutional clients... across 30+ releases". LLM tooling (a golden-copy config generator, a "retrieval-backed knowledge-base assistant", a "recursive skill-optimization framework"). HedgeServ integration "reaching the UAT milestone ahead of schedule". A "$225M principal-value discrepancy to a mis-scaled Tradeweb FIX tag". Azure DevOps and Datadog.
- At CRD: an internal AI agent for triage, "raising the FIX team's ticket closure rate 71.4% within the pod", and TLS certificate automation cutting alerts by more than 67%.
- AJ-Algo-Trader as a "research-to-production platform" with "17 external data feeds" and "1,028 tests green in CI".
- I found no confirmation in memory for the $225M tag, 10+ clients, 30+ releases, Readystate, or "Fortune-500". Check them with AJ before using them.

**The 8/28 resume.** It was probably the Somerville-header build. That build still said HedgeServ "production go-live", ">1000% reduction" and "Apr 2026 – Present", all of which are now banned. I could not prove which of two builds was uploaded (see uncertainties).

**What he said on the 9/25 call**
- "almost 3 years of experience in trading technology."
- Integration specialist most recently. Before that, FIX subject matter expert and senior associate analyst at a large tech company "part of a bank called State Street". About two years at Deloitte and an RIA (registered investment adviser) as associate wealth advisor. Undergrad in finance. MS in business analytics and AI at NYU. "understanding how to orchestrate data is something I really want to grow."
- **Proud project: the Adroit to HedgeServ integration.**
  - Drop-copy orders (copies of each trade) went to the competing OMS (order management system). The trader wanted Adroit as the front end but had to keep the other OMS "for compliance and back office... accounting reconciliation."
  - It took several months. He learned the other OMS's workflows from its support staff and ran the project in Excel.
  - He said the FIX spec grew "by over 50%" and that it was delivered "a month ahead".
- "I was a primary analyst for 5 clients."
- "a live phone queue as well as a rotation of over 200 clients for Charles River." This figure appears nowhere else in the record.
- Why Exa: the idea "very obviously needs to exist", the Agent Ultra post, and his client-facing history.
- Hobbies: cycling, yoga, cooking, video games, philosophy.
- **Not discussed:** the trading research pipeline, Snapshot, comp, NYC timing, or production servers. Ryan will hear the pipeline story for the first time (it is on paper only).

**Thank-you to Sukhm** mentioned technical evaluations, helping customers get more out of Exa, long-term projects, his manager's interest, the benchmark post and philosophy.

## 3. AJ's domains, ranked by how credibly he can say "I know this customer"

The pain-point links below are my ideas for the demo. None of them has been tested against Exa.

**1. Buy-side trading and investment operations at asset managers.** Charles River Development / State Street Alpha, Senior Associate FIX Analyst, Nov 2023 to Apr 2026 (two and a half years).
- **Work:** FIX connectivity and broker onboarding onto the Charles River Network, custom tag mappings, allocations (MsgType J) and DTCC CTM (automated post-trade matching), FIX 4.0/4.2 to 4.4 migrations, custom trade placement screens and blotter automation, Compliance certification, and Bloomberg TLS certificate automation. He also triaged security reference data problems with the data services team, who taught him what a "golden copy security" is and how to tell "which provider may have been the cause" (Alpha FMC call, same transcript).
- **End users:** PMs and traders who called him directly, desk operations, algo developers, sell-side brokers, client IT. He was primary FIX contact for five clients.
- **First-hand pain:** bad security reference data "would bust trades". The analyst then had to rebuild what changed about an instrument and which vendor was wrong. Web evidence (issuer press releases, exchange notices, corporate-action news), dated and linked, could let an ops analyst confirm the real-world event before escalating to a data vendor. Licensed data (Bloomberg, Refinitiv) stays the system of record; Exa would be the corroboration layer.

**2. Fixed-income electronic trading and OEMS vendor onboarding.** Adroit Trading Technologies, Integration Specialist, full-time, Apr to Aug 2026.
- **Work:** the HedgeServ OMS integration to client UAT (user acceptance testing), six revisions of Adroit's own FIX spec, the Charles River REST APIs (security reference data, pre-trade compliance, place trade), gRPC, Tradeweb, MarketAxess and ICE Bonds flows, the golden-copy config generator, the unmapped-values harness, and Datadog.
- **End users:** fixed-income traders at buy-side firms, client operations, HedgeServ support staff.
- **First-hand pain:** every client sent a security master in its own undocumented dialect, and fields silently defaulted. Public issuer and deal announcements could help confirm the identity of an unmapped bond. This is weaker than #1 because the pain was data mapping, not research.

**3. Quant and equity research data.** AJ-Algo-Trader, his own paper-trading research system. It started as the Stern capstone in about June 2026 (first paper trades June 24); he has built it alone since the team pivoted in August.
- **Work:** collectors for many feeds, with every source indexed by the date the market could have known it. A vintage diff (comparing every historical version of the file) showed zero restatements in the licensed panel. An LLM sentiment scorer reached 0.92 directional accuracy against a 0.45 lexicon baseline. Trials were pre-registered, and most came back null.
- **End user:** AJ himself. This is his strongest "I built it" story, and it matches the 8/28 essay's claim that retrieval was the bottleneck.
- **First-hand pain:** his eligibility audit found only 73 of 107 names had enough attention sources to ever fire. Point-in-time correctness was also the hardest discipline. Exa search with published-date filters (startPublishedDate and endPublishedDate are real parameters, per exa.ai/docs/reference/search) could fill coverage gaps without lookahead.
- **Limit:** he has not worked inside a quant fund. The Providence Investment Management summers are his own account, with duties unconfirmed.

**4. Compliance: auditor independence and KYC-style entity research.** Deloitte & Touche, Mar 2021 to May 2022.
- **Work:** he started as Private Investments Project Manager, then became Associate Analyst, Tracking & Trading. He evaluated private investment assets in Refinitiv for SEC, PCAOB and firm-policy conflicts; reclassification cut workload 75%. He ran independence audits of firm leaders, worked on the Broker Data Import Program, and used Tableau pre-clear tracking.
- **End users:** Deloitte professionals pre-clearing personal investments, and the independence team.
- **First-hand pain:** deciding whether a private entity is tied to an audit client means researching who owns or runs it. Exa's own Agent Ultra post lists "KYC compliance research" and "company enrichment". This fits the product closely, but his experience is older and junior.

**5. Wealth management at an RIA.** The Colony Group, Associate Wealth Advisor, May 2022 to Mar 2023.
- **Work:** a Tamarac reporting model across a $1.2B book, eMoney plans, HiddenLevers and Monte Carlo analyses, alternative-asset subscriptions via CAIS, two direct reports, and client-facing pre-sales support.
- **End users:** advisors and high-net-worth households.
- **Possible use:** meeting-prep briefs on client holdings or alternative funds.
- **Caution:** the exit is sensitive, so never volunteer anything about it.

**6. Energy and grid data for AI data-center siting.** Watt's Next capstone, weeks old, team project. He owns the data-engineering lane and wrote the EIA demand PR #72. Low authority.

## 4. Do-not-say list (fact corrections)

**The research system and his tenure**
- **"Production" for the trading system.** Say "paper-trading research system". The Sales_Engineering resume says "research-to-production platform", so if asked: research platform with live paper execution, paper only.
- **Charles River tenure.** Say two and a half years (Nov 2023 to Apr 2026), never three. The 8/28 Exa essay said three; if it comes up, correct it and move on.
- **Total trading-tech time.** Say "just under three years" (he told Sukhm "almost 3"), never four. Broad experience including Colony and Deloitte is about five years; the resume says "Five years".
- **Time spent on the trading system.** Do not repeat "the last two years" from the 8/28 essay. The work dates from spring and summer 2026.

**Clients and the 71.4% number**
- **Client count.** He was primary FIX analyst for FIVE clients, not three. He said five on the call. Client names (Connor, Clark & Lunn; Fred Alger; Glenmede) never go on slides.
- **What 71.4% means.** It is the pod's count of closed FIX L1 cases rising 231 to 396 from 2023 to 2024 after he joined the queue. It is not his closure rate and not "71.4% of my tickets."
- **His personal share.** He closed 226 of 396 (57%), about four times his three teammates' average and 3.0x the next closest. This is interview-only; always pair it with the visibility lesson (section 5) and never say "4x anyone".

**Adroit facts**
- **The FIX spec revisions** were ADROIT revising its OWN spec to expand the product, not HedgeServ changing. Canonical wording is "supported trade coverage grew 50%+". He told Sukhm "FIX spec by over 50%", so keep it close to that.
- **HedgeServ outcome.** It reached client UAT ahead of schedule. Never say go-live, production or delivered. He said "a month ahead" on the call; an earlier resume session deliberately dropped the one-month version as unconfirmed, so slides should say "ahead of schedule".
- **Employment type and title.** Adroit was full-time, never contract. The title is Integration Specialist. Dates were April to August 2026; never "Present".
- **The exit line** is two sentences: "It was a full-time role at a roughly 20-person vendor. The job turned out not to match the job description, so we parted amicably in August and I moved on." Never say fired or laid off.

**Other facts**
- **Education.** The MS is in progress, class of 2027. Never "finished".
- **Banned phrases:** ">1000% reduction" and "over 70%".
- **On-call level.** Weekend on-call was L2; the noon to 4 PM shift was L1.
- **Location.** Cambridge, MA, moving to NYC. Never Somerville.
- **"We" vs "I".** He built AJ-Algo-Trader alone, so say "I". Do not reuse the Komodo essay's "six-person team platform" framing.
- **Pre-sales.** Yes, via Colony client work, but no quota and no closed deals.
- **Mismatched pipeline numbers.** The resume Exa holds says 17 feeds and 1,028 tests. The prep script says "several dozen" feeds and "about 970" tests. The FDE resume says "10+ feeds". Pick one set with AJ, or skip the counts.
- **Benchmark names.** If he cites the Agent Ultra post, the competitors are Opus 5.5, GPT-6 Astra and Perplexity.
- **Unconfirmed claims to avoid unless AJ confirms them:** the Providence "best performing in 08-09" line (his own words, unverified), plus the resume items listed in section 2.
- **Never volunteer:** Swell Oyster, BMG 360, or anything about why he left Colony.

## 5. His known weak spot and how the demo narration should counter it

**The pattern: his reasoning is invisible while it happens.** He pattern-matches, jumps straight to the answer, and skips steps out loud. The evidence:
- At CRD he was told he did not escalate enough and that the team did not know what he was doing.
- oneZero rejected him on "troubleshooting process".
- On the Marex screen he declined a long story ("complex and lengthy") and asked no questions.

His speed was never the problem. What worked at the Invisible screen: short concrete proof points plus three questions back.

**New evidence from 9/25.** On the Alpha FMC call the same day:
- He could not answer the GET/POST/PUT question.
- He first proposed a simple average of returns before being led to weighting by market value.
- He needed coaching on indexes and materialized views.

Sukhm also had to pull the "why" out of the Adroit story.

**How the demo should counter it**
1. **Open with the customer, not the build.** Say who the user is, what they are trying to decide, and what it costs today. Then show the app.
2. **Narrate every step as a hypothesis.** "This analyst needs X. I'm sending Exa this query with these parameters because Y. If Exa is doing its job we should see Z." Then show it, then say what the user does next.
3. **Be fluent in the API.** Exa search is `POST https://api.exa.ai/search` with an `x-api-key` or `Authorization: Bearer` header. Main parameters include query, type, numResults, category, includeDomains, excludeDomains, startPublishedDate, endPublishedDate and contents (verified at https://exa.ai/docs/reference/search). He should be able to explain every parameter he sets and why.
4. **Timebox failure on purpose.** Have a cached result ready. If a live call is slow or wrong, say so, show what he would check, and switch to the fallback. That is the "timebox, announce, escalate" line from the visibility memory.
5. **Use "short version:" for any long story,** and never decline one.
6. **Ask questions back.** Include two or three discovery questions for Ryan, such as which verticals NYC FDEs cover (Sukhm named none) and what strong candidates do in this round. Also name honest limits, for example that Exa is the evidence layer and does not replace licensed data.

## 6. Tools on his machine that speed up the build (checked 2026-09-29)

**Python 3.11.9**
- Installed: streamlit 1.59.1, pandas 2.2.3, plotly 6.8.0, requests 2.34.2, httpx 0.27.2, pydantic 2.13.4, python-dotenv, uvicorn 0.49.0, anthropic SDK 0.120.2, google-genai 2.16.0, python-pptx 1.0.2 (for the 2-3 slides), python-docx, reportlab, yfinance 1.4.1, alpaca-py 0.43.4.
- **NOT installed:** Exa's Python SDK (exa_py), fastapi, flask, openai, gradio.
- Plain `requests` against the endpoint above works with no new install.

**API keys**
- No Exa API key exists in any .env I checked. AJ must create one himself on Exa's site.
- AJ-Algo-Trader/.env holds Alpaca, Gemini and Marketaux keys (names only, values not read). There is no Anthropic key there; memory confirms only Gemini is available, and the shared Gemini key hit 429 rate limits after about 3 agent runs.

**Streamlit experience.** He shipped the Citibike and weather dashboard (BigQuery plus Streamlit, deployed on Cloud Run). A Streamlit app is the fastest credible applet.

**n8n**
- The global CLI is installed (`C:\Users\ajwal\AppData\Roaming\npm\n8n`). It was not running and not re-verified.
- Node v24.18.0 and npm 11.16.0 are present.
- Jarvis-AI (Documents/Jarvis-AI) has working n8n workflows and a start script, and he has an n8n Cloud workspace (msbai).

**Lovable:** the team project exists, but credits were exhausted as of 9/16. Do not depend on it.

**Reusable code**
- AJ-Algo-Trader (Documents/AJ-Algo-Trader): knowable-date collectors and the LLM sentiment scorer.
- ai_agent_eval (Documents/ai_agent_eval): the writer, verifier and Python guard pattern. Useful for "every claim cites an Exa URL".

**Other tools**
- Installed: gcloud CLI, GitHub CLI, Claude Code, Word (COM automation), Chrome headless for PDF.
- R 4.6.0 is installed at C:\Program Files\R but is not on PATH. It is not needed for this build.
- Docker is not installed.

## Relevant local paths
- C:\Users\ajwal\Downloads\Tailored_CVs\Interview_Prep\Exa_Sukhm_Kang_Intro_Call_2026-09-25.md
- C:\Users\ajwal\Downloads\Tailored_CVs\Interview_Prep\Exa_Capstone_Pipeline_Script_2026-09-25.md
- C:\Users\ajwal\Downloads\Tailored_CVs\Interview_Prep\AlphaFMC_Exa_thank_you_notes_2026-09-25.md
- C:\Users\ajwal\Downloads\Tailored_CVs\APPLICATION_ESSAYS.md (lines 80-84, 4939-4951)
- C:\Users\ajwal\Downloads\Tailored_CVs\Upload\Sales_Engineering\Aidan_Walsh_Resume.pdf (the 9/20 resume; same hash as Interview_Prep\_send_20260925\Aidan_Walsh_Resume_OPTIMOVE_Sales_Engineering.pdf)
- C:\Users\ajwal\Downloads\Tailored_CVs\Upload\Forward_Deployed_AI\Aidan_Walsh_Resume.pdf (the current FDE build)
- C:\Users\ajwal\Downloads\Tailored_CVs\Upload\_backup_pre_fable_20260828\Forward_Deployed_AI_Aidan_Walsh_Resume_SOMERVILLE.pdf (probable 8/28 upload)
- C:\Users\ajwal\Downloads\Tailored_CVs\application_log.csv (Exa rows 381, 3692, 4205, 4843, 4869, 4993)
- C:\Users\ajwal\AppData\Local\Temp\claude\C--Users-ajwal\de92077b-64e0-4838-979e-5add8ad34faf\scratchpad\msg0.txt (full plain-text transcript: Exa call on lines 1-175, Alpha FMC call after that)