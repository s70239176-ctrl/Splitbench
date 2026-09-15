# Splitbench

Splitbench is one GenLayer Intelligent Contract with two modes and one jury:

- **HUMAN / Deal**: client and provider wallets, typically one 10,000-bps milestone.
- **AGENT / Job**: the same spending wallets, plus ERC-8004 agent-ID labels,
  immutable Agent Card snapshots, an A2A task pointer, and multiple milestones.

Lifecycle: `open (GEN locked) → submit → adjudicate (jury transaction) → PENDING → attest finality → ACCEPTED → settle → FINAL`.

`Accepted is not final. Appeal the adjudicate transaction through GenLayer before
attesting and settling it.`

## Step 0 — verified implementation findings

The contract uses the current documentation's required first-line runtime hash
`py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`, typed
`TreeMap[str, str]` / `DynArray[str]` storage (which GenVM provisions from
annotations; do not instantiate in `__init__`), payable `gl.message.value`, and
the documented EOA external-message transfer interface. `gl.nondet.*` calls are
inside `gl.vm.run_nondet_unsafe`; only consensus-agreed output is written after
the block. The validator checks JSON structure, award range, verdict family,
exact verdict when partials are enabled, and a 500-bps award tolerance. It never
compares LLM reason prose.

**API mismatch / finality limitation:** current contract context exposes no
transaction ID or transaction-lifecycle lookup. Therefore it cannot honestly
verify that its own `adjudicate` transaction has finalized. V1 explicitly gates
settlement: a job party must call `attest_finalized_adjudicate(job, mid, txId)`
after external verification, and `settle(job, mid, txId)` requires the exact
recorded value. `get_milestone` exposes `last_adjudicate_tx`. This is a testnet
bridge and must be replaced by a reviewed finality oracle or protocol primitive
before production custody.

## Why there is no `appeal()`

Appeals belong to GenLayer Optimistic Democracy, not this contract. On an
Accepted transaction, obtain the current charge immediately before appeal:

```ts
const charge = await client.getAppealCharge({ txId });
await client.appealTransaction({ txId, value: charge });
```

Use `genlayer appeal` from the CLI as the equivalent. Do not re-run the jury in
an on-contract appeal method.

## HUMAN example

1. Client calls payable `open("HUMAN", provider, brief, milestonesJson, deadline, true)` with GEN.
2. Provider calls `submit(jobId, "m1", '["https://example.com/evidence"]')`.
3. Anyone calls `adjudicate(jobId, "m1")`.
4. Wait through the protocol appeal/finality lifecycle, then a party records the finalized adjudicate tx ID.
5. Anyone calls `settle(jobId, "m1", txId)`.

## AGENT / A2A example

Open with mode `AGENT` and non-empty client and provider agent IDs. Resolve
those agent IDs off-chain to their wallets first (see `scripts/resolve_8004.md`).
Either party binds the task ID and full card snapshots. The provider maps A2A
Task artifacts into the URI list passed to `submit`; the jury, not A2A, grades.
See `a2a/skill.md`.

## Money and close paths

Every milestone weight must sum to 10,000. `settle` pays
`total * awarded_bps / 10000` to provider and refunds its slice balance to the
client; the final milestone receives any integer-division remainder on the
client side. `timeout_refund` works after the deadline only if the milestone was
not submitted/final. Mutual close requires two different parties and is only
allowed before any settlement, avoiding an unsafe global-split reconciliation
after partial payouts.

## Deploy

```powershell
genvm-lint check contracts/splitbench.py
genlayer deploy --contract contracts/splitbench.py --rpc https://studio.genlayer.com/api
genlayer network set testnet-bradbury
genlayer deploy --contract contracts/splitbench.py
```

The GenLayer CLI and linter were not installed in this workspace, so deployment
and direct-mode execution were not performed here. `tests/test_splitbench.py`
covers portable payout and protocol-guard assertions. With GenLayer Test
installed, add direct-mode cases for HUMAN open/submit, invalid weights,
non-provider submit, pre-adjudication settlement, timeout, mutual close, AGENT
IDs, card snapshots, and an integration `adjudicate` run (the latter needs a
Studio/local provider capable of web+LLM nondeterminism).

## Frontend dashboard

The React/Vite dashboard in `frontend/` connects an EIP-1193 wallet through
GenLayer JS. It supports contract configuration, fee-estimated writes, job and
milestone reads, escrow opening, evidence submission, adjudication, finality
attestation, settlement, timeout refund, and mutual-close flows.

```powershell
Copy-Item frontend/.env.example frontend/.env
# Set VITE_SPLITBENCH_ADDRESS to your deployment address.
npm install
npm run dev
```

Set `VITE_GENLAYER_NETWORK` to `studionet`, `testnetBradbury`, or
`testnetAsimov`. The selected browser wallet must be connected to that same
network. Escrow value is distinct from the fee estimate and is passed as the
payable transaction value.

## Security notes

- The jury is only `adjudicate`; there is no buyer override.
- Snapshot Agent Cards and briefs; never re-fetch a mutable card URI to alter a deal.
- Evidence is untrusted prompt input. Keep schemas tight and URLs reviewable.
- Appeals need funds; query `getAppealCharge` rather than hardcoding a charge.
- The finality attestation is a documented limitation, not cryptographic proof.
