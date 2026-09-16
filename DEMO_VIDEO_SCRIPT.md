# Required hackathon demo video (2–3 minutes)

1. Introduce Splitbench: native-GEN escrow for a HUMAN deal or AGENT job.
2. Show the deployed contract in the Studio Next explorer and its address in
   the deployed Vercel frontend configuration.
3. Connect a wallet on chain ID 61997 and open a one-milestone HUMAN deal.
   Point out Transaction Kit's live fee quote and the separate escrow value.
4. Switch to the provider wallet, submit a public evidence URL, then call
   `adjudicate`. Show the jury result in `get_milestone`.
5. Explain that appeal is protocol-level: use the adjudicate transaction's
   current appeal quote; Splitbench does not re-call an LLM in `appeal()`.
6. After the transaction finalizes, show finality attestation and settlement.
   Explain the explicit v1 attestation limitation and show the payout record.
7. Briefly show AGENT mode: IDs and immutable A2A card snapshots are bound;
   agent identity is a label while wallet authority remains the signer.

Include the Studio Next explorer URL and deployed Vercel URL in the video
description and project submission.
