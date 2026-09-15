# ERC-8004 resolver (off-chain v1)

Splitbench stores agent IDs and immutable Agent Card snapshots, but does not call
an ERC-8004 registry from GenVM. Before an AGENT-mode `open`, an operator should
read the Identity Registry at `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` on a
network where it exists, resolve each agent ID, and verify that its registered
wallet equals the intended Splitbench client/provider wallet. Record the card
text passed to `bind_a2a`; never resolve a mutable URI at adjudication time.

This is deliberately off-chain: a registry call is not consensus-safe here
without a deployed, reviewed interface for the target GenLayer network.
