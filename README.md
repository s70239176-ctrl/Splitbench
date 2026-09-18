# Splitbench

> **Before submitting:** replace the two `YOUR_...` placeholders below with the live Vercel URL and finalized Studio Next contract address. Reviewers should never have to guess where the application or contract is deployed.

## Project summary

Splitbench is an intelligent escrow layer for human and agent-to-agent work. A client creates an onchain job, locks GEN, and defines the terms and review rubric. The provider submits a public evidence URL for a milestone. GenLayer validators then independently assess that evidence against the stored rubric; only an approved milestone can be settled to the provider. This makes decentralized judgment meaningful: neither the client nor the provider can unilaterally decide whether work met the agreement.

## Live demo

- App: **https://splitbench-frontend.vercel.app/**
- Demo video: **https://x.com/stunnerr101/status/2100459738592850211**

## Contract details

| Item | Value |
| --- | --- |
| Network | GenLayer Studio Next (`studio-dev` SDK/CLI identifier) |
| Chain ID | `61997` |
| RPC | `https://studio-next.genlayer.com/api` |
| Explorer | `https://explorer-studio-dev.genlayer.com/` |
| Contract | `0xc461a6c917Ae98EAEF17f27153EFc8EbDfcCf093` |
| Explorer link | `https://explorer-studio-dev.genlayer.com/address/0xc461a6c917Ae98EAEF17f27153EFc8EbDfcCf093` |

The deployable Studio Next contract is [`contracts/splitbench_studio_next.py`](contracts/splitbench_studio_next.py). It persists the job terms, wallets, escrow amount, milestones, evidence, jury score, jury reason, and settlement state onchain.

## Tech stack

- **Frontend:** React 18, TypeScript, Vite
- **Wallet and transaction UX:** `genlayer-js` 2.0.0 RC1 and GenLayer Transaction Kit RC2
- **Contract:** Python GenLayer Intelligent Contract using Studio Next storage, nondeterministic consensus, and native GEN transfers
- **Network:** GenLayer Studio Next, chain ID `61997`

## How it works

1. The client connects a Studio Next wallet and opens a job with a provider address, delivery terms, a jury rubric, a deadline, milestones, and a non-zero GEN escrow.
2. The contract stores the client/provider roles, escrow, job details, and a record for each milestone.
3. The provider submits a public URL containing the completed work or other verifiable delivery evidence.
4. The client calls `adjudicate`. GenLayer's leader and validators evaluate the evidence against the stored rubric using consensus-backed nondeterminism.
5. Splitbench records `APPROVED` or `REJECTED`, plus a score and concise jury reason. An approved milestone can be settled to the provider; rejected work remains unpaid. After a deadline, the client can invoke a timeout refund.

## Run locally

### Prerequisites

- Node.js 22 LTS
- A browser wallet with a funded Studio Next account
- A finalized deployment of `contracts/splitbench_studio_next.py`

### Install and configure

```bash
git clone https://github.com/s70239176-ctrl/Splitbench.git
cd YOUR-REPOSITORY
npm install
cp frontend/.env.example frontend/.env
```

Set the actual contract address in `frontend/.env`:

```dotenv
VITE_SPLITBENCH_ADDRESS=0xYOUR_FINALIZED_SPLITBENCH_CONTRACT_ADDRESS
VITE_GENLAYER_NETWORK=studio-dev
```

Start development or produce the production build:

```bash
npm run dev
npm run check
npm run build
```

Open the local URL printed by Vite. Connect the wallet, enter the contract address if it is not already configured, and use the workflow below.

## Deploy the frontend to Vercel

Import this GitHub repository into Vercel and set **Root Directory** to `frontend`. Add the following Production, Preview, and Development environment variables:

```dotenv
VITE_SPLITBENCH_ADDRESS=0xYOUR_FINALIZED_SPLITBENCH_CONTRACT_ADDRESS
VITE_GENLAYER_NETWORK=studio-dev
```

Do not add a private key or seed phrase to Vercel. The user signs transactions from their browser wallet.

## Demo evidence / reviewer test data

Use **two different Studio Next wallets**: one client and one provider. Set a fresh Unix deadline in the future.

### Open job (client wallet)

| Field | Paste this value |
| --- | --- |
| Provider wallet | `0x7255FFA64b297c3Af0064Ec56f07bEEF1C04f2ef` |
| Job title | `Responsive landing page implementation` |
| Terms | `Build a responsive landing page with a hero section, feature section, and contact CTA.` |
| Jury rubric | `Approve only if the submitted page is publicly reachable, responsive, includes a hero, features, and a contact CTA, and has no obvious broken layout.` |
| Milestone count | `2` |
| Escrow value (wei) | `1000000000000000000` |
| Deadline | A future Unix timestamp |
| Client agent ID | `client-demo-001` *(optional)* |
| Provider agent ID | `provider-demo-001` *(optional)* |

The escrow value is 1 GEN in wei. Transaction fees are quoted separately by Transaction Kit and must be approved in the wallet.

### Submit and judge (provider then client)

1. After `open` finalizes, note its returned job ID, such as `SB-1`.
2. Switch to the **provider** wallet and submit milestone index `0` with a public, working URL that satisfies the rubric—for example your deployed landing page.
3. Switch to the **client** wallet and call `adjudicate` for that same job ID and milestone index.
4. Load the milestone in the Job Console. Reviewers should see the artifact, status, `jury_score`, and `jury_reason` recorded by the contract.
5. If the status is `APPROVED`, call `settle` from the client wallet and then reload the milestone. Its status becomes `PAID` and the contract transfers that milestone's GEN to the provider.

For a negative test, submit an unreachable URL or a URL that clearly does not meet the rubric. The jury should return `REJECTED` with an explanation instead of releasing escrow.

## Known limitations

- Studio Next is a test network. GEN, state availability, fee policy, and validator behavior can change or reset.
- Jury assessment depends on public evidence URLs. Private, expiring, geo-blocked, or unavailable pages cannot be reliably verified.
- AI judgment is constrained by the stored rubric, but it still has normal model limitations. It is not legal arbitration or a guarantee of objective correctness.
- Nondeterministic validator review and transaction finalization can take longer than ordinary EVM transactions. Refresh the UI after a transaction finalizes.
- This prototype supports equal escrow allocation across the job's milestones. It does not yet support custom per-milestone amounts or dispute evidence from both parties.

## Roadmap

### Phase 2

- Per-milestone descriptions and escrow allocations
- Provider-side evidence history and richer job activity timeline
- Structured evidence sources such as GitHub PRs, deployment checks, and test reports

### Phase 3

- Agent discovery and ERC-8004 reputation signals
- Dual-party dispute submissions and specialized review rubrics
- Production-ready finality and appeal integrations
- Analytics for job completion, verdict quality, and agent-provider reputation

## Repository structure

```text
contracts/splitbench_studio_next.py  Studio Next Intelligent Contract
frontend/                            React/Vite application
frontend/src/genlayer.ts             Wallet, Studio Next, and Transaction Kit setup
frontend/src/fee-profile.json        Transaction fee profile
DEPLOY_STUDIO_NEXT.md                Studio Next deployment notes
```
