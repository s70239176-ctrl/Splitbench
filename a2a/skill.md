# Splitbench Agent Card

Splitbench is an escrow settlement skill. Methods: `open`, `bind_a2a`, `submit`,
`adjudicate`, `settle`, and `challenge_via_protocol_appeal`.

Create an A2A task, then bind its task ID plus both card snapshots with
`bind_a2a`. Map Task artifacts (URLs, repository links, rendered deliverables)
to the JSON URI list for `submit`. The A2A service does not grade work and must
never attempt to emulate adjudication: the GenLayer `adjudicate` transaction is
the sole jury. To challenge it, use the GenLayer protocol appeal operation on
that transaction before finalization; there is intentionally no `appeal()` call.
