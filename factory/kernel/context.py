"""RLM is a CONTEXT mechanism, not an evolution one -- prime-agent name it Recursive Language
Models and the pattern is: keep the large object in the REPL as a variable and let the model
query it by writing code, rather than loading it into a prompt. A ledger, a run trace, a DOM
serialisation of 201 elements and a body of exchanges are all things this system has and none of
them should ever enter a context window whole. Measured upstream at 100x context extension and
2-3x token efficiency. llm_batch is the same idea for fan-out, and is what
capability/variations.py should ride.
"""
