# Break Check demo runbook

**Interview:** Exa, Forward Deployed Engineer (NYC), demo walkthrough
**When:** Friday 2026-10-02, 6:30 to 7:00 PM ET (prep block 5:30 to 6:30 is on the calendar)
**Where:** Google Meet, https://meet.google.com/gwq-danw-zek
**Interviewer:** Ryan Ahern (technical go-to-market, based in San Francisco; exact title not confirmed)

This file is the one to have open on the second screen. The full design is in `design\spec_v3.md`.

## 1. The demo in four sentences

1. **Who:** a security master analyst at an asset manager. Their job is to keep the firm's master record of every security correct.
2. **Problem:** every morning two data vendors disagree on some securities (a "break"), and the analyst has until the 9:30 open to find proof of who is right, by hand.
3. **What Exa does:** one plain-language search brings back the issuer's own announcement or the exchange notice as structured fields with a passage and a link, in about 3 seconds. The same search, with no event named, finds events that NEITHER vendor has yet. That is the climax.
4. **Why it is safe:** plain code, not a model, matches the evidence to the holdings and the vendor records, and the app says so honestly when it only has one source or found nothing.

## 2. The one habit that matters most

Say your reasoning out loud BEFORE you click. Every scene has four spoken parts:

| Part | What you say |
|---|---|
| Hypothesis | "I expect to see X, because Y." |
| Action | "So I am going to press Check, which sends these two requests." |
| Result | "It came back with X. That matches." or "That is different from what I expected." |
| If different | "If that had come back empty, the next thing I check is Z." |

The app shows these four lines for each row in the "Presenter notes" panel, so you never have to remember them.

If something breaks live: say what you see, say what you think it is, give it 30 seconds, then switch the sidebar to "Saved runs only" and say that you did.

## 3. Day-of checklist

**At 5:30 PM (start of prep block)**
- [ ] Laptop plugged in. Close Slack, email and every tab you do not need.
- [ ] Open a terminal in `C:\Users\ajwal\Documents\exa-demo` and run `streamlit run app\app.py`.
- [ ] Live: press Check on ONMD. Confirm both columns fill and the label reads corroborated.
- [ ] Live: run the watchlist scan once. Confirm the "Absent from both vendor records" finding appears. If Exa's index changed and it does not, use "Saved runs only" for that scene tonight and say so.
- [ ] Live: CDT and CTNT once each. Note what the labels say tonight.
- [ ] Turn on "Saved runs only", run the scan and ONMD again, confirm they match. Turn it off.
- [ ] Open `slides\break_check.pptx` in PowerPoint on slide 1.
- [ ] Open this runbook on the second screen.
- [ ] One full run out loud against a timer. Scene 5 should end by minute 20.

**At 6:20 PM**
- [ ] Join the Meet link to test camera, microphone and screen share.
- [ ] Share the browser WINDOW with the app, not the whole screen, so the terminal and this runbook stay private.
- [ ] Browser zoom at 125 percent so the fields are readable on a shared screen.
- [ ] Water within reach.

**Never on screen:** the `.env` file, the terminal, the Exa dashboard key page.

## 4. The script, minute by minute

**The story in one line:** reconciling two feeds can only find where they disagree. It can never find what both are missing. Exa can.

**Every scene has four spoken parts: hypothesis, action, result, and "if it comes back different, I check X next".** Say the hypothesis BEFORE you click.

**Timing at a glance**

| Clock | Scene | What it proves |
|---|---|---|
| 0:00 to 1:30 | Slide 1: why Exa, and why this workload | The thesis |
| 1:30 to 3:30 | Slide 2: the customer, the queue, the mock portfolio | You understand the workflow |
| 3:30 to 4:30 | Slide 3: the one idea | Where Exa fits |
| 4:30 to 7:30 | Scene 1: resolve one known break (ONMD) | Fast, grounded retrieval |
| 7:30 to 11:30 | Scene 2: the watchlist scan finds an event both feeds missed | Exa creates new operational value |
| 11:30 to 14:00 | Scene 3: affected holdings and the proposed action | Evidence becomes work |
| 14:00 to 17:00 | Scene 4: CDT date ambiguity, then one incomplete result | Sound judgment |
| 17:00 to 20:00 | Scene 5: Ryan picks an issuer, no event named | It generalizes |
| 20:00 to 23:00 | Slide 4: impact, cost, proof of concept | Commercial depth |
| 23:00 to 30:00 | Questions, both ways | |

**If running long:** cut Scene 4's second half (the incomplete result) first, then shorten Scene 5 to one run. Never cut Scene 2.

**0:00 to 1:30. Slide 1: why Exa.**
Open on the thesis, not the customer: "Reconciling two feeds can only find where they disagree. It can never find what both are missing. Exa can, and I will show you it doing that in about seven minutes." Walk one row of the table, the first one: finds an event you did not name. A keyword feed only finds what someone tagged, a scraper only reads the page you pointed it at, a model alone, with no retrieval, has nothing to cite and nothing fresher than its training data. Then the right card in one breath: it finds what reconciliation cannot, it is cheap to prove, and it is the workload that gets Exa approved inside an asset manager.

**1:30 to 3:30. Slide 2.**
Tell it as the team's morning: the shared queue, the 9:30 deadline, the CDT break on the slide, what a wrong or late fix breaks. Then the line that sets up the climax: "And the worse case is the one the queue never shows you: both vendors agree because both are missing an event."
Credibility line, word for word: "I spent two and a half years at Charles River as the primary FIX analyst for five buy-side clients. When security reference data was wrong, trades busted, and I was the one working out with the trader and the data team which provider caused it." Never name a client.

**3:30 to 4:30. Slide 3.**
"Licensed feeds stay the record. Exa supplies the evidence for their exceptions, and for their gaps." Walk the five boxes. Say plainly: "The vendor records in this demo are simulated. Every announcement you will see is real and retrieved by Exa."

**4:30 to 7:30. Scene 1: resolve one known break (ONMD).**
- **Hypothesis:** "OneMedNet did a 1-for-10 reverse split. Vendor A has a new CUSIP, Vendor B shows no change. Two independent sources should settle it: the company's own release and the Nasdaq notice. I expect both back in three or four seconds, both printing 68270C202."
- **Action:** on the "Break queue" tab, ONMD is selected. Press "Check ONMD". While it runs, say what the two requests are: one query per source type, type auto, highlights on, the rules in the system prompt.
- **Result (measured):** both found. Issuer prints "68270C 202" with a space, Nasdaq prints "68270C202". Code strips the space. Label: "Corroborated by two independent sources". Pick the new_cusip field in the evidence view so the supporting sentence shows. "That is the whole pattern: source passage, extracted field, proposed action. Code decides, the analyst approves." Press Approve.
- **If different:** if a column is empty, open the "Identity guard" panel to see whether the right page came back and was dropped. If the live call is slow past the timebox, the saved run from Sep 29 shows with a label saying so.

**7:30 to 11:30. Scene 2: the scan. The climax.**
- **Hypothesis:** "Now the question reconciliation can never answer. Here is a mock portfolio of 10 securities with what each vendor shows. I am going to ask Exa, for each issuer, for recent corporate action announcements WITHOUT naming an event. Code will match whatever comes back to the holdings and to both vendor records. If both feeds are missing something, it should land in the queue with the sentence that proves it. I expect about ten seconds for the whole list, and at least one name where neither vendor has the event."
- **Action:** the "Watchlist scan" tab is already open. Press "Scan watchlist". Narrate the progress line as the rows come in.
- **Result (measured today, 1:20 PM):** 11 seconds, $0.07 for ten names. Counters: 2 absent from both vendor records (AGRZ, NFE), 3 present at one vendor only (CTNT, TRUG, BAC), 3 both vendors have it (ONMD, CDT, JAGX), 2 nothing found (MSFT, PG, the quiet names). In "Open a finding" pick "AGRZ: Absent from both vendor records": Agroz 1-for-20 reverse split, effective Sep 29, new CUSIP G0136M119, two independent sources (Nasdaq alert 682 plus the PR Newswire release). Read the supporting passage out loud and click the link so the page is on screen.
- **The Exa point:** "No scraper for this issuer's site. No event named. One plain-language search per issuer, and the finding comes back as structured fields with the passage it came from. That is what I cannot build with a keyword feed."
- **If different:** if the scan finds nothing for the expected name, say "nothing found is not proof nothing happened" and open the saved run with "Saved runs only". If an unexpected finding appears, read its passage before trusting it, and say that is exactly why the analyst approves.

**11:30 to 14:00. Scene 3: what the analyst does with it.**
- **Hypothesis:** "A changed CUSIP is abstract. The analyst needs to know what it touches."
- **Action:** scroll to "What the analyst sees next" under the AGRZ finding. Then pick "BAC 06051GLX5" in "Open a finding" for the bond.
- **Result:** held shares before and after the split (AGRZ: 20,000 shares become 1,000 at 1-for-20, before fractional handling), the open orders flagged for review, the identifier update proposed. "Holdings never leave the building. Only the public identity goes to Exa." For the BAC note: held par, the expected cash event to verify, and the action is "propose the status update for analyst verification", because an announcement of a future redemption does not prove it completed.
- **If different:** if a number looks off, say the holdings are mock and the arithmetic is one line in compare.py that Ryan can read.

**14:00 to 17:00. Scene 4: judgment. CDT, then one incomplete result.**
- **Hypothesis (CDT):** "Vendor A says effective Sep 28, Vendor B says Sep 29. I expect both to be right: the issuer's release should say effective Sep 28 at 5 PM, after the close, and the Nasdaq notice should say trading on new terms from the 29th."
- **Action:** Break queue, CDT, press "Check CDT".
- **Result (measured today):** both found. Issuer release: 1-for-25, CUSIP 20678X700, "September 28, 2026, at 5:00 pm, Eastern Time". Nasdaq alert 683: effective Sep 29. Label "Corroborated by two independent sources" with the explained difference: legal effective date versus first trading day. "That rule is fixed code in compare.py. Both vendors are right about something. The next step is on our side: check which effective-date mapping the golden copy reads." (On Tuesday alert 683 was not in Exa's index and the row read "Single source, issuer only"; the saved run still shows that. If asked: Exa indexed it during the week.)
- **Incomplete result (about 60 s):** CTNT. "Here Exa's stored copy of the exchange notice is a placeholder page. Code notices, makes one live re-fetch for a tenth of a cent, and gets the real notice. The label still says one source and the analyst confirms." If asked: on Tuesday morning that re-fetch came back empty once; code treats an empty success as a failure.
- **If different:** if alert 683 drops out again, the row reads "Single source, issuer only" and still shows the explained difference from the issuer release alone. Either way the date rule holds.

**17:00 to 20:00. Scene 5: Ryan's pick, no event named.**
"Pick any issuer from the watchlist, or type one." Keep the event unspecified.
- **Hypothesis (say it before pressing):** "Same search, same code, an issuer I did not prepare. If it has announced a corporate action in the last two months, I expect it back with a passage and a link. If not, the app says nothing found, which is not proof that nothing happened."
- **Action:** "Free-form row" tab, "Live challenge: scan one name". Choose "Type an issuer name or ticker", type it, press "Scan this name".
- **Result:** read the status and the passage, or the "Nothing found. Not proof nothing happened." line. A typed name has no vendor records, so the status reads "Found (typed name, no vendor records to compare)". Test today: "Nuwellis" came back with a reverse split mentioned inside an earnings release, terms "not stated", and the line "The value is not printed word for word in this passage; open the link to confirm." Say: "That is a mention, not an announcement. The app says so, and the action is to open the link, not to book anything."
- **If it comes back empty:** "Nothing passed the identity check, so the app says not found rather than guessing. Next I would widen the window from 60 days and check the listing venue."

**20:00 to 23:00. Slide 4.**
Breaks still open at 9:30 first, then analyst time (assumptions, say so), then the measured Exa spend, then the proof of concept. Add the production line: "In production this scan is an Exa Monitor per issuer: recurring search, deduplication, webhook delivery, structured findings. Tonight it is on demand." Close with the discovery questions on the slide.

**23:00 to 30:00. Questions, both ways.** Section 6 below. The first three are the ones to ask if time is short.

**Backup material, only if asked:** the simulated timeout (sidebar toggle), the thread pool and cache design, the inventory of missing Nasdaq alerts, auto versus deep-lite. All of it is on the "Under the hood" tab and in section 5.

## 5. Prepared answers

Ryan is likely to open the code and point at a line. Say each of these out loud once before Friday.

- **Why POST?** "The request carries a JSON body with the query, filters and schema, and Exa defines search and contents as POST endpoints; GET reads something at a URL with no body, POST sends a body for the server to act on, and PUT replaces a resource at a known address."
- **What does the x-api-key header do?** "It tells Exa which team is calling, for authorization, billing and rate limits; it's read from .env on the server and never reaches the browser, and Exa also accepts it as an Authorization Bearer header."
- **What happens to a running thread when the timebox fires?** "Nothing stops it, because Python can't kill a running thread: the screen stops waiting and shows the saved run, and the thread finishes when Exa answers or its own request timeout fires, then writes to the working cache for next time."
- **Why is the cache keyed by a hash of the request body?** "So the same request always maps to the same file and any change to the query, type or dates maps to a new one, which means a saved answer can never be shown for a different question; sorting the keys first makes key order irrelevant."
- **How long did the build take?** "About four hours of build and rehearsal, plus research and a morning of keyed testing beforehand, and about an hour timing myself on the manual baseline; I used AI tools for research and code, as your posting says is expected, and I reviewed every call myself." (The last clause is true only once the 20-minute explain-the-code pass is done.)
- **Why a thread pool at module level?** "A with-block waits for every thread on exit, which would turn my 8-second timebox into the full request timeout."
- **Why not exa-py?** "exa-py's get_contents adds 10,000 characters of text whenever I don't pass text, summary or extras, even when I ask only for highlights. That bills two content types, and it drops the per-URL error tags. search() adds text only when you pass no contents. With raw HTTP, the body on screen is exactly what was sent."
- **Why eight schema fields when Exa prefers five?** "Your patterns page prefers one to five root fields. I measured eight flat fields, and on every call where the right page was in the index all eight came back filled, so I kept the shape I measured. Six of them feed a rule in compare.py. The other two, identifier_in_source and event_type, are display only. Identity is decided by code against the cited page's own text, because on the CDT exchange call the model returned 'CDT' as the identifier at low confidence while citing another company's alert. That is the prompt being echoed, and it is exactly what the grounding check catches."
- **What if the live re-fetch fails?** "It did once, on Tuesday morning: status success with an empty page. Code treats an empty success as a failure and hands the row to the analyst as not confirmed. A few hours later the same call returned the real page, so the row now reads repaired. Either way a person signs off, and the failure is the evidence I'd bring to Exa for a recrawl or a custom index."
- **Why does the app keep things in st.session_state?** "Streamlit runs the whole script again from the top every time someone clicks anything, so ordinary variables are wiped on each click. I keep the check results, the call log and the approvals in session_state, which Streamlit keeps for each browser tab across those reruns."
- **Why save the result as soon as Check is clicked?** "A button is True only on the one rerun that its click causes. So I save the result right away, and later clicks like Approve redraw from the saved result without calling Exa again."
- **What is on_tick?** "It is a small function defined inside run_check that I hand to evidence.py, which calls it back every half second while it waits. It redraws one placeholder on screen, so a timer counts up and evidence.py never needs to know about Streamlit."
- **Why strip spaces from a CUSIP before comparing?** "One source prints 68270C 202 and another prints 68270C202. A plain text comparison would call that a conflict when it is the same security."
- **How does the row get its label?** "The rules in row_label run top to bottom and the first one that fits wins, so a conflict always beats an agreement. It is plain code, so the same evidence gets the same label every time, with a reason an auditor can read."
- **Why is a field missing when Exa says confidence is high?** "High confidence on a value of not stated means the model is sure the page says nothing. A confident nothing is still nothing, so code reads the value and ignores the label."
- **Why the approved domain list and not the open web for the scan?** "I tried both today. With no domain list the same events came back, but through syndicators, and one quiet name, Procter and Gamble, came back as a redemption because of a Form 25 on a syndicator page. That is a debt delisting, not an action on the shares we hold. With the approved list every event came back from the issuer or the exchange and both quiet names stayed quiet. For a security master the list is the customer's and the false positive is the thing to avoid."
- **Why does the scan not name the event?** "Because the point is to find what we do not know. The query asks for any recent corporate action by that issuer; the system prompt says which kinds count and which to ignore, like dividends. Code matches whatever comes back to the holdings and the vendor records."
- **How would this run in production?** "One Exa Monitor per held issuer: a recurring search with the same body, deduplication, webhook delivery and structured findings. Tonight the scan is on demand because Monitors need a public webhook and are not covered by zero data retention; under ZDR it runs as a daily scheduled search."

## 6. Questions for Ryan

Drawn from `research\interviewer.md`. Credit his work accurately: the Pydantic AI PR was closed, and in the harness integration that shipped he was one contributor among several, so say "the Exa capability in the Pydantic AI harness you worked on".

**Ask these three first if time is short**
1. "In Pydantic AI issue 6082 you described a customer whose model was putting domain filters into the query text. How common are setup mistakes like that, and is catching them part of an FDE's first weeks on an account?"
2. "A workload like Break Check spends very little, but it's the one that gets Exa through InfoSec and zero data retention at an asset manager. How does Exa size an enterprise commitment when the first workload is small but opens the door?"
3. "Which verticals is the NYC FDE team going after first? Is financial services where the early pipeline is?"

**About his work**
4. "Do partner integrations like the Exa capability in the Pydantic AI harness start from a specific customer ask, or are they a way to meet developers inside the frameworks they already use?"
5. "You pushed highlights as the default for agents because they use fewer tokens. In a POC, how do you show a customer the tradeoff between answer quality and token cost in numbers they trust?"
6. "Your agent_run change in the MCP server handles runs that outlast the call window. For enterprise Agent customers, what causes the most production pain: latency, cost control, or structured-output quality?"
7. "You added the x-exa-integration attribution header. How does the go-to-market side use usage signals like that, for example to spot expansion or churn risk?"
8. "Your post about joining Exa described years of manual research feeding executive and architecture decisions. What convinced you to move from doing that research to building the tool for it?"

**About the product, from building this demo**
9. "Two Exa pages list zero-data-retention coverage for Contents and Answer differently. Which is current, and how do FDEs handle a security questionnaire when the docs disagree?"
10. "Snapshot is the strict point-in-time tool. What do customers use it for most, and how is the 100-request limit usually handled in a trial?"
11. "In discovery, how do FDEs decide between Search, the Agent API and Monitors? Is there a rule of thumb?"
12. "In the CTNT scene, Exa's stored copy of a Nasdaq alert was a placeholder, another alert from the same week wasn't indexed, and the live re-fetch failed once and worked a few hours later. When a customer has a source they can't do without, what's the usual fix: a recrawl request, a custom index, or something else, and who on Exa's side owns it?"

**About how FDE work is judged**
13. "When an enterprise demo lands, what's usually the moment that does it: results they couldn't get elsewhere, structured output, or speed?"
14. "How do you set POC success criteria with an enterprise team, and who on their side usually signs off?"
15. "After a strong demo, where do deals most often stall: security review and data retention, procurement, or proving return on investment?"
16. "What separates the FDEs who ramp fastest here from the ones who struggle?"

**About the NYC FDE team**
17. "How will NYC FDEs split time between new logos and existing accounts, and does each FDE pair with a specific account executive?"
18. "How do SF and NYC FDEs share demos and integration patterns? Is there a shared demo library, or will the new Technical Enablement role own that?"
19. "The posting says ship code in the morning and close a deal in the afternoon. How literal is that? Roughly what share of the week is building versus calls?"
20. "When an FDE finds a product gap, how does it get back to product? Can FDEs ship fixes into core repos directly, the way you did with the MCP server?"
21. "What would you want a new NYC FDE to have shipped or owned by day 90?"

## 7. Facts to keep straight

| Say this | Not this |
|---|---|
| Two and a half years at Charles River | Three years |
| Primary FIX analyst for five buy-side clients | Three clients |
| Paper-trading research system | Production trading system |
| Reached client UAT ahead of schedule | Went live a month early |
| Integration Specialist at Adroit, full time, April to August 2026 | Contractor |
| "A client" or "one of my buy-side clients" | Any client name |
| "Zero data retention is available on search. I would confirm the other endpoints with you." | "Everything is covered by zero data retention." |
| "The vendor values are mocked. Every source page is real and retrieved by Exa." | Anything that implies the vendor data is real |

## 8. Today, before 5:30

- [ ] Read section 4 once, start to finish.
- [ ] One timed run out loud. Scene 5 should end by minute 20.
- [ ] Say the prepared answers in section 5 once without notes, especially the three about the scan.
- [ ] Open these pages in a browser and confirm what you will say: Nasdaq alert 2026-682 (AGRZ), alert 2026-683 (CDT), the CDT GlobeNewswire release of Sep 25, the Bank of America Sep 4 redemption release.
- [ ] Word your own answer to "how long did the build take". It has to be true as you say it.
- [ ] Decide whether to mention the paper-trading research system. The demo stands without it.
