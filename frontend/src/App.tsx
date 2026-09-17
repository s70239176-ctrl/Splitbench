import { FormEvent, useMemo, useState } from 'react';
import { GenLayerTransactionPanel } from '@genlayer/transaction-kit-react';
import '@genlayer/transaction-kit-react/styles.css';
import { connectWallet, networkName, readClient } from './genlayer';

const configured = (import.meta.env.VITE_SPLITBENCH_ADDRESS || '') as `0x${string}`;
const isAddress = (v: string) => /^0x[0-9a-fA-F]{40}$/.test(v);
const short = (v?: string) => v ? `${v.slice(0, 6)}…${v.slice(-4)}` : '—';

type Notice = { kind: 'ok' | 'error' | 'info'; text: string } | null;
export default function App() {
  const [address, setAddress] = useState<string>(configured);
  const [wallet, setWallet] = useState('');
  const [jobId, setJobId] = useState('');
  const [mid, setMid] = useState('0');
  const [data, setData] = useState<any>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState('');
  const [kit, setKit] = useState<unknown>(null);
  const [pendingTx, setPendingTx] = useState<unknown>(null);
  const ready = isAddress(address);
  const contract = useMemo(() => address as `0x${string}`, [address]);

  const connect = async () => {
    try { const { account, kit: connectedKit } = await connectWallet(); setWallet(account); setKit(connectedKit); setNotice({ kind: 'ok', text: `Connected ${account}` }); }
    catch (e) { setNotice({ kind: 'error', text: message(e) }); }
  };
  const write = async (functionName: string, args: unknown[], value?: bigint) => {
    if (!ready) return setNotice({ kind: 'error', text: 'Enter a valid deployed Splitbench address first.' });
    if (!kit) return setNotice({ kind: 'error', text: 'Connect your Studio Next wallet before starting a transaction.' });

    setBusy(functionName);

    const tx = {
      kind: 'write' as const,
      address: contract,
      method: functionName,
      args,
      ...(value !== undefined ? { userValue: value } : {}),
    };

    // The RC2 React transaction panel omits userValue for payable calls.
    // Use Transaction Kit directly for open(), which carries the escrow.
    if (value !== undefined) {
      try {
        const transactionKit = kit as any;
        const quote = await transactionKit.estimate({ preset: 'standard' }, tx);
        const submitted = await transactionKit.submit(quote, tx);
        setNotice({
          kind: 'ok',
          text: `Escrow transaction submitted: ${submitted.genlayerTxId}. Wait for finalization, then load the job.`,
        });
      } catch (error) {
        setNotice({ kind: 'error', text: message(error) });
      } finally {
        setBusy('');
      }
      return;
    }

    setPendingTx(tx);
    setNotice({ kind: 'info', text: 'Review the fee quote and sign the transaction in the Transaction Kit panel.' });
  };
  const load = async (milestone = false) => {
    if (!ready || !jobId) return setNotice({ kind: 'error', text: 'Enter a valid contract address and job ID.' });
    setBusy('read');
    try {
      const result = await readClient().readContract({ address: contract, functionName: milestone ? 'get_milestone' : 'get_job', args: milestone ? [jobId, BigInt(mid)] : [jobId], jsonSafeReturn: true });
      setData(typeof result === 'string' ? JSON.parse(result) : result); setNotice({ kind: 'ok', text: `${milestone ? 'Milestone' : 'Job'} loaded from latest chain state.` });
    } catch (e) { setNotice({ kind: 'error', text: message(e) }); }
    finally { setBusy(''); }
  };
  const onOpen = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const f = new FormData(event.currentTarget);
    try {
      const amount = BigInt(String(f.get('amount')));
      const milestoneCount = BigInt(String(f.get('milestoneCount')));
      if (milestoneCount < 1n || milestoneCount > 20n) throw new Error('Milestone count must be between 1 and 20.');
      write('open', [String(f.get('provider')), String(f.get('title')), String(f.get('terms')), String(f.get('rubric')), milestoneCount, BigInt(String(f.get('deadline'))), String(f.get('clientAgent') || ''), String(f.get('providerAgent') || '')], amount);
    } catch (e) { setNotice({ kind: 'error', text: message(e) }); }
  };
  const onSubmitEvidence = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const f = new FormData(event.currentTarget); try { write('submit', [String(f.get('jobId')), BigInt(String(f.get('mid'))), String(f.get('artifact'))]); } catch (e) { setNotice({ kind: 'error', text: message(e) }); } };

  return <main>
    <nav><a className="brand" href="#top">split<span>bench</span></a><div className="nav-meta"><span className="network">{networkName}</span><button onClick={connect}>{wallet ? short(wallet) : 'Connect wallet'}</button></div></nav>
    <section className="hero" id="top"><div><p className="eyebrow">GENLAYER INTELLIGENT ESCROW</p><h1>Settle work with<br/><em>one shared court.</em></h1><p className="lede">Deal for people. Job for agents. Funds stay locked until the evidence jury and GenLayer finality process agree.</p></div><div className="flow"><span>Open</span><i>→</i><span>Submit</span><i>→</i><strong>Jury</strong><i>→</i><span>Final</span><i>→</i><span>Settle</span></div></section>
    <section className="config card"><div><p className="eyebrow">CONTRACT CONNECTION</p><h2>Point this dashboard at your deployment</h2></div><label>Splitbench contract address<input value={address} onChange={e => setAddress(e.target.value.trim())} placeholder="0x…" /></label><button className="primary" onClick={() => setNotice({ kind: ready ? 'ok' : 'error', text: ready ? 'Contract address saved for this session.' : 'That is not a 20-byte address.' })}>Save address</button></section>
    {notice && <div className={`notice ${notice.kind}`}>{notice.text}</div>}
    {kit !== null && pendingTx !== null && <section className="card tx-panel"><p className="eyebrow">LIVE STUDIO NEXT TRANSACTION</p><GenLayerTransactionPanel kit={kit as any} tx={pendingTx as any} network={networkName as any} trackUntil="finalized" onDone={() => { setBusy(''); setPendingTx(null); setNotice({ kind: 'ok', text: 'Transaction Kit completed tracking. Refresh the job or milestone state to verify the finalized result.' }); }} /></section>}
    <section className="grid">
      <article className="card span2"><p className="eyebrow">01 / CREATE ESCROW</p><h2>Open a Splitbench job</h2><form onSubmit={onOpen} className="form two"><label>Job title<input required name="title" placeholder="Landing page implementation" /></label><label>Provider wallet<input required name="provider" placeholder="0x provider address" /></label><label className="full">Terms<textarea required name="terms" placeholder="Describe exactly what must be delivered." /></label><label className="full">Jury rubric<textarea required name="rubric" placeholder="State what the GenLayer jury must verify before approving payment." /></label><label>Milestone count<input required name="milestoneCount" type="text" defaultValue="2" inputMode="numeric" /></label><label>Escrow value (wei)<input required name="amount" type="text" defaultValue="1000000000000000000" inputMode="numeric" /></label><label>Deadline (Unix seconds)<input required name="deadline" type="text" defaultValue={String(Math.floor(Date.now() / 1000) + 604800)} inputMode="numeric" /></label><label>Client agent ID (optional)<input name="clientAgent" placeholder="client-demo-001" /></label><label>Provider agent ID (optional)<input name="providerAgent" placeholder="provider-demo-001" /></label><button className="primary full" disabled={!!busy}>{busy === 'open' ? 'Submitting…' : 'Lock GEN & open escrow'}</button></form></article>
      <article className="card lifecycle"><p className="eyebrow">SAFETY RULE</p><h2>Jury before payment.</h2><p>The provider submits public evidence. GenLayer validators independently review it. Only an approved milestone can be settled.</p><div className="status"><b>SUBMIT</b><span>evidence</span><b>JURY</b><span>adjudicate</span><b>PAYMENT</b><span>settle</span></div></article>
      <article className="card span2"><p className="eyebrow">02 / JOB CONSOLE</p><h2>Read job state</h2><div className="form inline"><label>Job ID<input value={jobId} onChange={e => setJobId(e.target.value)} placeholder="SB-1" /></label><label>Milestone index<input value={mid} onChange={e => setMid(e.target.value)} placeholder="0" /></label><button onClick={() => load(false)} disabled={!!busy}>Get job</button><button onClick={() => load(true)} disabled={!!busy}>Get milestone</button></div>{data && <pre>{JSON.stringify(data, null, 2)}</pre>}</article>
      <article className="card"><p className="eyebrow">03 / PROVIDER</p><h2>Submit evidence</h2><form onSubmit={onSubmitEvidence} className="form"><label>Job ID<input required name="jobId" defaultValue={jobId} /></label><label>Milestone index<input required name="mid" defaultValue={mid} /></label><label>Public evidence URL<textarea required name="artifact" placeholder="https://your-project.vercel.app" /></label><button disabled={!!busy}>{busy === 'submit' ? 'Submitting…' : 'Submit evidence'}</button></form></article>
      <ActionCard title="04 / JURY" action="adjudicate" fields={[['Job ID', jobId], ['Milestone index', mid]]} onRun={() => write('adjudicate', [jobId, BigInt(mid)])} busy={busy} />
      <ActionCard title="05 / SETTLEMENT" action="settle" fields={[['Job ID', jobId], ['Milestone index', mid]]} onRun={() => write('settle', [jobId, BigInt(mid)])} busy={busy} />
      <article className="card span2"><p className="eyebrow">ALTERNATIVE PATHS</p><h2>Close safely without a jury result</h2><div className="quick"><ActionCard title="Timeout refund" action="timeout_refund" fields={[['Job ID', jobId]]} onRun={() => write('timeout_refund', [jobId])} busy={busy}/><ActionCard title="Request mutual close" action="request_mutual_close" fields={[['Job ID', jobId]]} onRun={() => write('request_mutual_close', [jobId])} busy={busy}/><ActionCard title="Finalize mutual close" action="finalize_mutual_close" fields={[['Job ID', jobId]]} onRun={() => write('finalize_mutual_close', [jobId])} busy={busy}/></div></article>
    </section><footer>Splitbench v1 · Native GEN escrow · <a href="https://docs.genlayer.com/" target="_blank">GenLayer documentation</a></footer>
  </main>;
}
function ActionCard({ title, action, fields, onRun, busy }: { title:string; action:string; fields:[string,string][]; onRun:()=>void; busy:string }) { return <article className="card action"><p className="eyebrow">{title}</p><h2>{action}</h2>{fields.map(([n,v]) => <label key={n}>{n}<input readOnly value={v}/></label>)}<button onClick={onRun} disabled={!!busy}>{busy === action ? 'Submitting…' : action}</button></article>; }
function message(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object') {
    const value = error as Record<string, unknown>;
    const candidates = [value.shortMessage, value.message, value.reason, value.details, value.data];
    for (const candidate of candidates) {
      if (typeof candidate === 'string' && candidate.trim()) return candidate;
      if (candidate && typeof candidate === 'object') {
        const nested = candidate as Record<string, unknown>;
        if (typeof nested.message === 'string' && nested.message.trim()) return nested.message;
      }
    }
    if (typeof value.code === 'number' && value.code === 4001) return 'Wallet connection was rejected.';
    try { return JSON.stringify(error); } catch { return 'Wallet connection failed with an unknown provider error.'; }
  }
  return 'Wallet connection failed with an unknown error.';
}
