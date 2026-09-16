declare module '@genlayer/transaction-kit' {
  export function createTransactionKit(config: {
    chain: unknown; provider: unknown; account: `0x${string}`; suggestions?: unknown;
  }): unknown;
}
declare module '@genlayer/transaction-kit-react' {
  import { ComponentType } from 'react';
  export const GenLayerTransactionPanel: ComponentType<{
    kit: unknown; tx: unknown; network: string; trackUntil?: 'decided' | 'finalized';
    onDone?: (outcome: unknown) => void;
  }>;
}
declare module '@genlayer/transaction-kit-react/styles.css';
