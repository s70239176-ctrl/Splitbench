"""Studio Next / Consensus v0.6 deployment reminder.

Use a matching GenLayer CLI v0.40 RC release family and a measured fee profile:
  genlayer network set studio-dev
  genlayer network info
  genlayer deploy --contract contracts/splitbench.py --fee-profile frontend/src/fee-profile.json

Do not auto-deploy from this file: deployment requires the operator's funded
wallet and the resulting contract address must be reviewed before it is placed
in Vercel's public VITE_SPLITBENCH_ADDRESS environment variable.
"""

print("See DEPLOY_STUDIO_NEXT.md before deploying.")
