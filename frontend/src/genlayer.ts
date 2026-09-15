import { createClient } from 'genlayer-js';
import { studionet, testnetAsimov, testnetBradbury } from 'genlayer-js/chains';

export type NetworkName = 'studionet' | 'testnetBradbury' | 'testnetAsimov';
export const networkName = (import.meta.env.VITE_GENLAYER_NETWORK || 'studionet') as NetworkName;
export const chain = { studionet, testnetBradbury, testnetAsimov }[networkName];
declare global { interface Window { ethereum?: { request(args: { method: string }): Promise<string[]> } } }
export function readClient() { return createClient({ chain }); }
export async function walletClient() {
  if (!window.ethereum) throw new Error('No compatible browser wallet found.');
  const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
  const account = accounts[0] as `0x${string}` | undefined;
  if (!account) throw new Error('Wallet returned no account.');
  const client = createClient({ chain, account, provider: window.ethereum as any });
  await client.connect(networkName);
  return { client, account };
}
export async function submitWrite(request: { address: `0x${string}`; functionName: string; args: unknown[]; value?: bigint }) {
  const { client, account } = await walletClient();
  const estimate = await client.estimateTransactionFeesForWrite(request as any);
  const txId = await client.writeContract({ ...request, fees: { distribution: estimate.distribution, feeValue: estimate.feeValue } });
  return { txId, account };
}
