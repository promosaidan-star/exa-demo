# Interviewer research: Ryan Ahern (Exa), for the Fri 2026-10-02 6:30 PM ET demo round

## 1. Who he most likely is

**Bottom line:** I found one Ryan Ahern who works at Exa. Two separate public sources tie him to the company, his GitHub account and his LinkedIn. I am **highly confident** a Ryan Ahern works at Exa, and **fairly highly confident** he is the person AJ will meet, since no other Ryan Ahern links to Exa. His **exact title is not confirmed anywhere public.**

### Evidence he works at Exa (high confidence)
- **GitHub profile `ryahern`**: the name is Ryan Ahern, the company field says "Exa.ai", the location says San Francisco and the website field says exa.ai. Source: https://github.com/ryahern (read through https://api.github.com/users/ryahern).
- **His code commits use a work email at Exa**, `rahern@exa.ai`. They are on his pull requests (proposed code changes) to Pydantic AI, the Pydantic AI Harness and Exa's own MCP server. Sources: https://api.github.com/repos/pydantic/pydantic-ai/pulls/6237/commits and https://api.github.com/repos/exa-labs/exa-mcp-server/pulls/383/commits
- **Merged commits in Exa's official repo** `exa-labs/exa-mcp-server`, dated 2026-06-26, 06-30 and 07-16:
  - https://github.com/exa-labs/exa-mcp-server/pull/373
  - https://github.com/exa-labs/exa-mcp-server/pull/383
  - https://github.com/exa-labs/exa-mcp-server/commit/08242e3b8a9efdee9a8e945a33b68f283874010f
- **LinkedIn `linkedin.com/in/ryan-j-ahern`**: the headline is "Building @ Exa" and the location is San Francisco Bay Area. LinkedIn blocked a direct fetch (HTTP 999), so I read the headline from a DuckDuckGo search snippet of https://www.linkedin.com/in/ryan-j-ahern. I could not see his experience or education sections.
- **His own LinkedIn post, dated 2026-05-21**: he says why he joined Exa and announces the $250M Series C at a $2.2B valuation led by a16z. In his words, he joined to "build perfect search for agents." Source: https://www.linkedin.com/posts/ryan-j-ahern_years-ago-i-spent-my-days-scouring-the-globe-activity-7463017711267233792-SzAU (I read the full post text from the page's structured data.)
- **He is not on Exa's About page.** That page names 24 people and no Ryan. It lists only part of a company of about 100, so this does not count against him. Source: https://exa.ai/about

### Role: what the evidence points to (title unknown, medium confidence on the kind of work)
His public work looks like **technical go-to-market work**, meaning the technical side of selling: forward deployed, solutions or partner engineering. It does not look like pure core engineering or pure sales. The reasons:
- He writes production code with tests for **customer-facing integrations**:
  - Exa's MCP server. MCP (Model Context Protocol) is a standard way to plug tools like Exa into AI agents.
  - The Exa tools inside Pydantic AI, a popular Python framework for building agents.
- In a public GitHub issue he says the domain-filter change was prompted by **a customer configuration problem he was seeing**: the model was putting domain filters into the query text itself. Source: https://github.com/pydantic/pydantic-ai/issues/6082
- The Pydantic side describes the work as coming from **a partner collaboration with Exa**. A Pydantic maintainer also mentions a live call with him to agree the plan. Sources: https://github.com/pydantic/pydantic-ai-harness/issues/375 and https://github.com/pydantic/pydantic-ai/pull/6237
- He added an **integration attribution header** (`x-exa-integration`). It lets Exa see which partner integration a request came from, which is a go-to-market measurement concern. Source: https://github.com/pydantic/pydantic-ai/issues/6082
- The FDE job posting describes the role almost exactly this way: "ship code in the morning and close a deal in the afternoon", build demos and sample apps, and fix customer issues across the stack. Source: https://jobs.ashbyhq.com/exa/c542d672-691c-46c1-9741-856d66f2c2ea (full text read through Exa's public Ashby job API, https://api.ashbyhq.com/posting-api/job-board/exa).

He could also be a partner or ecosystem engineer, or a developer-relations engineer. The one fixed point is that the only public headline says "Building @ Exa."

### Where he sits and timing
- His LinkedIn and GitHub both put him in San Francisco. So 6:30 PM ET is 3:30 PM his time, and he is probably not on the NYC team day to day.
- He was at Exa by 2026-05-21, the date of the post. His first public Exa code is 2026-06-26. His exact start date is unknown.

### Prior employers (not found)
- His profile is blocked, so I could not confirm any prior employer.
- The only clue is his own post. He describes past years spent researching information for executive decisions, software architecture and product discovery. That points to a research, strategy, architecture or product-type background, but I found nothing that names a company.
- On GitHub he has one older contribution, a merged 2021 fix to matplotlib's build process (https://github.com/matplotlib/matplotlib/pull/21397). It shows long-standing Python and build-tooling comfort, nothing more.
- AJ can check the Experience section himself at https://www.linkedin.com/in/ryan-j-ahern. Note that viewing it while logged in may show Ryan the visit, which is normal before an interview.

### Other Ryan Aherns ruled out (none tied to Exa)
- Truveta co-founder and CMO (https://www.linkedin.com/in/ryan-ahern-3580b1108/)
- Highmetric Sr. Solution Architect in New York (https://www.linkedin.com/in/ryan-ahern-21678524/)
- Ingenico Head of Solutions (https://www.linkedin.com/in/ryan-ahern-a6942229/)
- Palo Alto Networks / CyberArk in Boston (https://www.linkedin.com/in/ryan-ahern-396161134/)
- Booz Allen (https://www.linkedin.com/in/ryan-ahern-b67971159/)
- A Skillsoft-linked marketing leader (https://www.linkedin.com/in/ryan-ahern-101/)
- CrestCura solar in Arizona (https://www.linkedin.com/in/ryandahern/)
- An actor and a concert pianist

The X account @ryandahern would not load (HTTP 402), and nothing ties it to him.

### What he has said publicly about Exa and search (paraphrased from GitHub threads he wrote)
- **Highlights by default for agents.** Exa's "highlights" return only the most relevant passages from each page, instead of full page text. He recommends them as the default for agentic search because they use fewer tokens. He also corrected a bot: full text is not deprecated, highlights are just the better default for most agent use. Source: https://github.com/pydantic/pydantic-ai/issues/6082
- **Steer away from old search types.** He wants developers nudged off the old `neural` and `keyword` search types and onto `auto`. Exa's docs now list instant, fast, auto, deep-lite, deep and deep-reasoning. Sources: https://github.com/pydantic/pydantic-ai/issues/6082 and https://exa.ai/docs/reference/search
- **`find_similar` is deprecated in the exa-py SDK.** He deprecated it in the Pydantic integration rather than extending it. Source: https://github.com/pydantic/pydantic-ai/pull/6237
- **Developers, not the model, should set domain filters.** `includeDomains` and `excludeDomains` should be set in code so the LLM cannot inject them into the query. Source: https://github.com/pydantic/pydantic-ai/issues/6082
- **No breaking changes, lots of tests.** His PR claims:
  - recorded-response tests (VCR tests, which replay saved HTTP responses so tests do not hit the live API)
  - 100% branch coverage on the Exa module
  - a checked box saying any AI-generated code was reviewed line by line by him

  Source: https://github.com/pydantic/pydantic-ai/pull/6237
- **One streaming agent tool.** In the MCP server he replaced four Agent tools with a single `agent_run` tool. It streams the run with server-sent events (SSE, a way for a server to push progress updates as they happen). If a run outlasts the roughly 750-second call window, it hands back a run ID instead of failing. The tests check that an early abort does not create a paid run. He also documented the limits under zero data retention (ZDR, Exa's enterprise mode where run data is not kept). Source: https://github.com/exa-labs/exa-mcp-server/pull/383
- **Correct errors for unauthorized calls.** He made unauthorized calls to protected tools return a proper 401 error instead of a confusing "method not found." Source: https://github.com/exa-labs/exa-mcp-server/pull/373
- **The Pydantic integration shipped.** His ExaAgent capability, which hands long research jobs to Exa's Agent API, and an optional summary mode were merged on 2026-07-21. Pydantic published a build guide the same day. Sources: https://github.com/pydantic/pydantic-ai-harness/pull/386, https://pydantic.dev/articles/harness-exa (author Bill Easton) and https://pydantic.dev/docs/ai/harness/exa-search/

## 2. What he will likely weigh most in the 30-minute demo

He builds and ships integrations and fixes customers' setup mistakes. So expect him to judge **whether AJ uses the API the way an expert would**, as well as **whether the story would land with a buyer**. In priority order:

1. **Current, correct API usage**
   - Use `type: auto`, or explain why you chose fast or deep instead.
   - Use highlights where an agent or model reads the output, and full text only where a human reads whole pages.
   - Set domain filters in code.
   - Avoid `findSimilar`, which he deprecated in the Pydantic integration because exa-py deprecated it.
   - Avoid the deprecated parameters in the docs: `livecrawl` (use `maxAgeHours`) and `context` (use `highlights` or `text`). Source: https://exa.ai/docs/reference/search
   - Be ready to open the code and explain each Exa call. His own PR checklist commits him to reviewing AI-written code line by line.
2. **Reliability and cost awareness**
   - His MCP work is all about timeouts, long runs, clean handoffs and not charging for aborted runs.
   - Show what the applet does on a slow or failed call.
   - If you use the Agent API, know the effort tiers. The docs list minimal $0.012, low $0.025, medium $0.10, high $0.50 and xhigh $1.00, with metered auto and ultra options. Source: https://exa.ai/docs/reference/agent-api-guide
   - Mention structured output: a JSON schema gives you schema-checked results with citations.
3. **Enterprise realism**
   - Name the end user, the workflow step it replaces, and what data governance would come up.
   - Under ZDR, run data is available only while the run executes and for 10 minutes after. `previousRunId` and premium data sources (Exa Connect) are unavailable. Source: https://exa.ai/docs/reference/agent-api-guide
4. **POC rigor**
   - Exa's EMEA FDE posting asks for someone who can "scope a POC with clear success criteria". POC means proof of concept, a trial build to prove value before purchase.
   - The same posting asks for someone who will say "I don't know, I'll find out." It also notes AI-assisted coding is expected and hand-crafted code is not the bar. Source: https://jobs.ashbyhq.com/exa/234bf118-672a-45d1-a4a2-02065d1c02f0
   - Have one baseline comparison ready, for example Exa results against the customer's current manual process.
5. **Audience-adapted narrative**
   - The FDE posting asks for pitching to CTOs, engineers and PMs alike.
   - Exa's Technical Enablement posting says Exa sells a technical product to technical buyers through a technical sales motion, and calls out "demo excellence" and the POV/POC process. Source: https://jobs.ashbyhq.com/exa/b193ad1c-7700-4e32-98cb-efc791993963
6. **Fit with agent frameworks (bonus points)**
   - A short line on how the applet's retrieval step could become an MCP tool or agent capability in the customer's stack would match his own work.

Note: Jenna's email says "walk us through," so there may be more than one person on the call.

## 3. Questions AJ could ask at the end (18)

**About his work**
1. I saw the Exa capability you built into the Pydantic AI harness. Do partner integrations like that start from a specific customer ask, or are they a way to meet developers inside the frameworks they already use?
2. In that Pydantic issue you mentioned a customer whose model was putting domain filters into the query text. How common are setup problems like that, and is catching them part of an FDE's first weeks with a new account?
3. You made highlights the default for agent use because they use fewer tokens. In a POC, how do you show a customer the tradeoff between answer quality and token cost in numbers they trust?
4. Your agent_run change handles runs that outlast the call window. For enterprise customers on the Agent API, what causes the most production pain: latency, cost control, or the quality of structured output?
5. You added an integration attribution header to the Pydantic client. How does the go-to-market side use usage signals like that, for example to spot expansion or churn risk?
6. Your post about joining Exa described years of manual research feeding executive and architecture decisions. What convinced you to move from doing that research to building the tool for it?

**About how FDE work is judged**
7. When an enterprise demo lands, what is usually the moment that does it: results they could not get elsewhere, structured output, or speed?
8. How do you set POC success criteria with an enterprise team, and who on their side usually signs off?
9. After a strong demo, where do deals most often stall: security review and data retention, procurement, or proving return on investment?
10. What separates the FDEs who ramp fastest here from the ones who struggle?
11. In discovery, how do FDEs decide whether a customer needs Search, Websets or the Agent API? Is there a rule of thumb?
12. What is one thing about Exa you wish more customers understood before their first technical call?

**About the NYC FDE team**
13. The NYC FDE and AE roles are both building the office from zero. How will NYC FDEs split time between new logos and existing accounts, and does each FDE pair with a specific AE?
14. How do SF and NYC FDEs share demos, integration patterns and lessons? Is there a shared demo library, or will the new Technical Enablement role own that?
15. Which verticals is NYC going after first? Financial services seems natural for New York. Is that where the early pipeline is?
16. The posting says ship code in the morning and close a deal in the afternoon. How literal is that? Roughly what share of the week is building versus calls?
17. When an FDE finds a product gap, how does it get back to product? Can FDEs ship fixes into core repos directly, the way you did with the MCP server?
18. What would you want a new NYC FDE to have shipped or owned by day 90?

## Extra context (verified, may help)
- **NYC FDE posting:** published 2026-08-13, in person in NYC, base $130K to $275K plus equity and bonus. Source: https://jobs.ashbyhq.com/exa/c542d672-691c-46c1-9741-856d66f2c2ea through https://api.ashbyhq.com/posting-api/job-board/exa
- **Pairing with an AE:** the EMEA FDE posting says FDEs pair with an Account Executive to own the technical win. The NYC posting does not say this, which is why question 13 asks.
- **The NYC office is new:** the NYC AE posting describes building the NYC go-to-market office from zero. Source: https://jobs.ashbyhq.com/exa/e3e0cd05-d71a-491d-a553-2a991741915c
- **AJ's own calendar entry** for the round also records Ryan's title as "not confirmed." Gmail has no message naming his title.