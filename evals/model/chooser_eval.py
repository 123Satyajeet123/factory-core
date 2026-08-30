"""D1, D2 and D7 from gates/model-vendor.md, against models that cost nothing.

    uv run --with python-dotenv python -m evals.model.chooser_eval

NEEDS A CREDENTIAL AND SPENDS NOTHING. Three models, four asks each -- economical on
purpose. The question is whether a model that costs nothing can answer in the shape and say
"none of these", not which model is best.

Economical on purpose: three models, four asks each. The question is whether a free model
can answer in a nested schema and say "none of these" -- not a benchmark.
"""
import asyncio
import os

from dotenv import load_dotenv

from factory.model.driver import Refused, ask
from factory.model.schemas_resolve import Chosen, situation

load_dotenv(".env")
KEY = os.environ["OPENROUTER_API_KEY"]
BASE = "https://openrouter.ai/api/v1"

AMONG = {0: "button 'Save'", 1: "button 'Cancel'", 2: "textbox 'Name'",
         3: "link 'Inbox'", 4: "button 'Save draft'"}

CASES = [
    ("plain",      "press the button that commits the form", 0),
    ("near-miss",  "press the control that saves without sending", 4),
    ("none",       "press the button that deletes the account", -1),
    ("the field",  "type the person's name", 2),
]

FREE = ["nvidia/nemotron-3.5-lightning:free",
        "minimax/minimax-m3:free",
        "thinkingmachines/inkling-small:free"]

async def main():
    conforming = 0
    for model in FREE:
        conformed = right = 0
        notes = []
        for name, wanted, expect in CASES:
            got = await ask(situation(wanted, AMONG), Chosen,
                            models=[model], key=KEY, base_url=BASE)
            if isinstance(got, Refused):
                notes.append(f"{name}=REFUSED({got.why[:34]})")
                continue
            conformed += 1
            picked = got.value.which
            ok = picked == expect
            right += ok
            notes.append(f"{name}={picked}{'' if ok else f'(wanted {expect})'}")
        print(f"{model:44} conformed {conformed}/4  correct {right}/4")
        print(f"{'':44} {' '.join(notes)}")
        conforming += conformed == len(CASES) and right == len(CASES)
    print(f"\nmodels that conformed AND chose correctly, including refusing: {conforming}")
    print("D2 holds by construction: every failure above is a typed refusal, not an exception.")

asyncio.run(main())
