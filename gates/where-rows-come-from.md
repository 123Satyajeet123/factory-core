# Where does a workflow get its rows?

Written **before** any of it exists. `run/harness.over` takes a sequence of rows from its
caller, so today somebody assembles them by hand and the "workflow" is the half after that.
P4 in gates/first-workflow.md predicted this, on a real task whose rows were prose in a chat.

## The question, and the trap

The obvious answer is a connector per destination -- read a spreadsheet, read a chat, read a
CSV. That is a lookup table with a bigger budget: it works on the destinations somebody
thought of and nothing else, and `evals/agnostic` exists to catch exactly that shape.

The observation this gate rests on: **the system already reads records from destinations it
knows nothing about.** `witness/readers/fetched.py` finds lists of objects sharing keys in
whatever a page fetched for itself, falls back to CSV, and names no site. A witness and a
source are the same act -- read records off a surface -- pointed at different moments.

So the hypothesis under test is that a Source is a SURFACE PLUS A READER, and that no new
reading machinery is needed.

## Candidates, named up front

- **`witness/readers`, reused** -- the readers already discovered through the entry point
  group, pointed at a surface before the run instead of after an act.
- **A connector per destination** -- named so that rejecting it is a decision. Expected to
  lose S2 outright.
- **A model asked to read the page** -- the expensive rung. Belongs in the ladder, not as
  the default, and it cannot be first because it would never get cheaper.
- **The person, every run** -- the honest baseline. It is what happens today.

## Criteria

**S1 no new reading machinery.** If a Source needs a reader that `witness/readers` cannot
already supply, say which and why rather than adding a second way to read records.

**S2 no destination is named in our source.** Which surface, and which field feeds which
parameter, are ANSWERS -- recorded on the workflow, entering through the question rail.
`evals/agnostic` applies unchanged.

**S3 a source that yields nothing is a question, not an empty run.** Zero rows and "the page
had none" are different, and a run that quietly does nothing is the worst of the three.

**S4 the mapping is checked before the run, not per row.** A source whose records lack a
parameter the workflow needs is a question asked once, with what the records DID carry
offered as the candidates.

**S5 rows are read on a channel that did not act.** The same rule the witness follows. A
source read off the DOM of a page we just drove is our own bytes coming back.

**S6 it survives the destination having more than the workflow needs.** Extra fields are
ordinary; the mapping names what is wanted and ignores the rest.

## Blind prediction

S1 holds and the reader is reused unchanged. **S5 is where I expect trouble**: a source is
naturally read from the page the person is looking at, and the honest channel is what that
page FETCHED, which exists only if the destination speaks structured data. On a surface that
paints its rows, there will be no admissible source at all -- and the right answer will be a
question rather than a DOM scrape.

If that holds, the coverage number already built (`paints, carries no structured body`) is
the same signal for sources as it is for verdicts, and nothing new is needed to report it.

## Result

(filled in by execution — not by reasoning)
