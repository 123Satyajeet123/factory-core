# A real workflow, read by me before the factory sees it

Written **2026-08-30, after watching a 15m54s screen recording and before any demonstration
is recorded.** This is my answer. When the same task is demonstrated live and compiled, the
induced program can be held against it — and where they differ, the disagreement says where
to look. Neither is ground truth: mine is a second opinion on the same evidence, and
SkillsBench is the reason it is not treated as more than that.

No person's name, address or company is written here. The task has a shape and the shape is
what matters; the identities are the operator's data and do not belong in this repo.

## The task, as I read it

Five surfaces, one loop.

1. **A chat assistant** — ask for a shortlist of companies. The answer is prose in a chat.
2. **A prospecting tool** — per company, filter people by employer, pick one by job title,
   press a per-row control that REVEALS a contact address that was hidden until then.
3. **A spreadsheet** — append a row: first name, address, company.
4. **The chat assistant again** — ask for a generalised message with a named variable in it.
5. **Mail** — compose per person, substitute the variable, send.

## What I expect the compiler to induce

    press   textbox 'Search'          on the prospecting tool
    write   textbox 'Search'          param: the company
    press   button/link  <a person>   chosen by job title
    press   button 'Access email'     the reveal
    ... then a spreadsheet write, then a compose and a send

## Where I predict the machinery fails, worst first

**P1 — TABS, and I think this is fatal today.** The workflow spans five surfaces in five
tabs. `session.attach` takes `context.pages[0]`, `browser/tabs.py` is one line, and nothing
in `core/workflow.Step` names a surface. A demonstration that moves between tabs will
record acts from one page and lose the rest. **This is the prediction I am most confident
about and it is not subtle.**

**P2 — the spreadsheet defeats `locate`.** It paints its grid to a canvas, so
`Accessibility.queryAXTree` will find no cell to press by role and name. `coverage` should
report `paints, carries no structured body` and name it as the reader to build. That is the
machinery working, not failing — but the step will not run.

**P3 — the reveal is where the witness should shine.** Revealing an address is a server
round trip; if it returns JSON, `Fetched` gets the value on a channel that did not perform
the act. If it does not, this workflow has no admissible witness anywhere in it.

**P4 — the rows do not come from anywhere addressable.** The list of companies is prose in
a chat. `core/workflow.Source` does not exist and `Workflow.params` expects a row mapping.
Somebody has to say what the rows are; that is a question, and the rail to ask it is unbuilt.

**P5 — sending mail is irreversible and nothing stops it.** `authority/permit.py` is empty.
A replay would send. Whatever else happens, that step must not run unattended before permits
exist.

**P6 — the chat prompts are typed text that varies between demonstrations**, so induction
may parameterise the PROMPT rather than the company. I expect at least one parameter that is
not one.

## What I expect to work

Induction finding the per-company parameter; the guard refusing on a moved control; the
recorder resolving role and name for ordinary form fields in the mail client, which has real
accessibility markup. Acts of reading and scrolling produce no acts at all, so sixteen
minutes of a person thinking should compile to a short program.

## How this gets settled

`factory demonstrate <task>` twice, then `factory compile <task>`, then this file gets a
Result section with what was induced beside what I wrote. A prediction that turns out wrong
is the useful outcome; the wrong outcome is quietly editing this afterwards.

## Result

(filled in after a demonstration — not before)
