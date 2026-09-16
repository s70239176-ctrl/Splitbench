# Studio Next deployment checklist

Splitbench targets the Consensus v0.6 preview (Studio Next): CLI `studio-dev`,
SDK `studioDevnet`, chain ID `61997`, canonical RPC
`https://studio-dev.genlayer.com/api`, and explorer
`https://explorer-studio-dev.genlayer.com/`. Do not use stable `studionet`.

## Fee profile

On v0.6 all deploys and writes need fee parameters. Use the matching RC
`gltest --fee-profile` tool and commit its output at
`frontend/src/fee-profile.json`. Cover deploy, `open` (one and many
milestones), `submit`, LLM/web `adjudicate`, finality attestation, settle,
timeout and mutual-close payout paths. The committed profile is intentionally
empty until it has actually been measured; Transaction Kit then safely requests
a live default quote for unmatched calls.

## Deploy

```bash
genlayer network set studio-dev
genlayer network info
genlayer deploy --contract contracts/splitbench.py --fee-profile frontend/src/fee-profile.json
```

Wait for finalization and a successful execution result before using the
returned address. Set Vercel `VITE_SPLITBENCH_ADDRESS` to it and
`VITE_GENLAYER_NETWORK=studio-dev`.

The dashboard uses Transaction Kit RC2 to quote fees, verify live fee policy,
fund the appeal posture, sign with the wallet, and track the transaction.
Payable escrow value and the protocol-fee deposit are separate.
