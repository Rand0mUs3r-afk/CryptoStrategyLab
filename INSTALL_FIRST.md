# Install this replacement bundle

This is a local file deliverable, NOT a GitHub commit or an already-running bot.
Upload the files at their matching paths in CryptoStrategyLab only.
Keep existing unlisted files, especially research.yml and all saved state branches.

1. Replace root alpaca_crypto.py, README.md and ALPACA_SETUP.md.
2. Add root alpaca_config.json.
3. Replace .github/workflows/alpaca-crypto-paper.yml and ci.yml at those exact paths.
4. Replace tests/test_journal_alpaca.py and add tests/test_alpaca_execution.py.
5. The remaining bundled files are unchanged copies of your uploaded dependencies.
6. Wait for Crypto lab tests to pass. Follow ALPACA_SETUP.md to check and enable tick.

Required secrets remain ALPACA_PAPER_KEY_ID and ALPACA_PAPER_SECRET_KEY for the NEW
paper account. Required variables: ALPACA_EXPECTED_PAPER_ACCOUNT_ID,
ALPACA_CRYPTO_DEDICATED_ACCOUNT=true, ALPACA_CRYPTO_PAPER_ENABLED=true.
The last variable permits order submission and automatic scheduled ticks.

Use check before enabling. Use tick to execute. Your already-created state branch
normally means initialize_new_state stays unchecked. If it belongs to the old account,
choose a new ALPACA_CRYPTO_STATE_BRANCH and initialize only that new branch.

Do not delete or reset broker/virtual ledgers. Do not upload files to ChatGptTrader.
No secrets, account IDs or broker state are included in this package.
