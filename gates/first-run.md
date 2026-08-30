# The first run: demonstrate, induce, execute, be told whether it worked

Not written before the code, because it is not a vendor decision. It is the record of what
connecting the drivers found, and it is here because every one of these was invisible while
each driver was exercised on its own.

## Result — 2026-08-30, by execution

    demonstrated 'Ada Lovelace': 3 acts
    demonstrated 'Grace Hopper': 3 acts
    induced      'add a person' params=('add_a_person',)
       press  textbox 'Name'
       write  textbox 'Name'   param='add_a_person'
       press  button 'Save'
    contract     expects={'name': 'Grace Hopper'} varies={'name': 'add_a_person'}
    ran 2 rows, destination went from 2 to 4
       Alan Turing        steps=[ok ok ok]  CONFIRMED
       Katherine Johnson  steps=[ok ok ok]  CONFIRMED
    control      a row that wrote nothing of the sort -> REFUTED
    written by the run: ['Alan Turing', 'Katherine Johnson']
    FAULTS 0

Two demonstrations became a program with a parameter; the program ran on rows nobody
demonstrated; the destination received exactly those rows; and a channel that did not
perform the writes said so.

## Five defects, none of which any driver's own suite could see

**1. Every character was typed twice.** `keyDown` carrying `text` inserts, and so does
`char`. The destination received `GGrraaccee HHooppppeerr`. Introduced by an earlier fix:
the recorder had shown `keys=0` because `char` alone fires no `keydown`, and adding all
three events overcorrected.

**2. The steps were emitted in dictionary order, not graph order.** `program.states` is a
mapping; the program is a graph with an `entry` and transitions. Iterating `.values()` gave
press, press, write, so a run pressed Save on an empty field and typed into nothing --
**and it ran clean**, three `ok`s and a confirmation.

**3. The write was recorded on `change`, which fires on BLUR.** So the ledger held press,
press, write for a person who had typed before saving. The compiler was faithfully
reproducing an order that never happened. Now `input`, coalesced per field, flushed before
whatever act ends it.

**4. `Did` reached the witness carrying no exchanges.** Every verdict was UNVERIFIABLE on a
run where every write landed. What a page fetched because of an act now travels with it.

**5. The field was never cleared between rows**, so values accumulated across them.

## The one that matters, and the eval nearly missed it

With the first four fixed the run reported **FAULTS 0** -- and both rows were CONFIRMED
against `name = 'Grace Hopper'`, the DEMONSTRATION's value. The witness was confirming each
row against a record the demonstration had written. True, and about neither row.

The check that catches it is a control, not an assertion about success: take the contract,
bind it to a row that wrote nothing of the sort, and require the verdict to MOVE.

    before   control -> confirmed     the verdict could not move, so it meant nothing
    after    control -> refuted

`Contract.varies` maps a field to the parameter whose value belongs in it, and
`for_row` binds it before witnessing. Which parameter is answered by what the varying step
actually took across the demonstrations -- not by `param_specs.example`, which holds the
first trace's value while the contract came from the second. They did not match, `varies`
stayed empty, and everything confirmed.

## What this run does NOT show

The destination here issues no idempotency key, so `identifies` is empty and CONFIRMED still
means PRESENT rather than CAUSED. The control shows the verdict tracks the row's value; it
does not show the act caused the record.

Nothing was promoted. No capability was manufactured. The demonstrations were driven by us,
so nothing here says a person's recording induces as cleanly.
