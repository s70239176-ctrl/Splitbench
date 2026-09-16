import { createClient } from 'genlayer-js';
import { studioDevnet } from 'genlayer-js/chains';
import { createTransactionKit } from '@genlayer/transaction-kit';
import feeProfile from './fee-profile.json';

export const networkName = 'studio-dev';
export const chain = studioDevnet;
declare global { interface Window { ethereum?: { request(args: { method: string }): Promise<string[]> } } }
export function readClient() { return createClient({ chain }); }
export async function connectWallet() {
  if (!window.ethereum) throw new Error('No EIP-1193 wallet found. Install or unlock a compatible browser wallet.');
  const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
  const account = accounts[0] as `0x${string}` | undefined;
  if (!account) throw new Error('Wallet returned no account.');
  const client = createClient({ chain, account, provider: window.ethereum as any });
  // The `studioDevnet` chain object already contains the Studio Next chain ID,
  // RPC and consensus contracts. RC client types do not accept a `studio-dev`
  // string here, so let the client connect using that configured chain.
  await client.connect();
  return { account, kit: createTransactionKit({ chain, provider: window.ethereum, account, suggestions: feeProfile }) };
}
