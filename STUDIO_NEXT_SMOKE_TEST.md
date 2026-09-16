# Studio Next smoke test

Run these after a fresh deploy on Studio Next (chain 61997) and retain the
transaction links for review.

1. `open` HUMAN with 10,000 wei and one 10,000-bps milestone; verify `job-0`.
2. Submit the milestone from the exact provider wallet; verify `SUBMITTED`.
3. Attempt provider submission from the client wallet; require rollback.
4. Adjudicate `https://example.com`; verify a JSON jury verdict and `PENDING`.
5. Verify the adjudicate transaction's lifecycle in the explorer. Only after
   finalization, record its ID, then settle and inspect both payments.
6. Open expired job and run `timeout_refund` before submission.
7. Open another job; have client propose and provider confirm mutual close.
8. Open AGENT mode without IDs (must revert), then with IDs and A2A snapshots.
9. In the frontend, submit at least one write through Transaction Kit and show
   the fee quote, policy verification, transaction status, and final outcome.
