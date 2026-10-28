# Local validation results

Build scope: local replacements based on the user's uploaded files. No GitHub writes,
no Alpaca authentication, no broker orders, no hosted workflow execution and no trading
performance measurement were performed by the assistant.

Command: `python -m pytest -q --color=no`

```
........................................................................ [ 66%]
....................................                                     [100%]
=============================== warnings summary ===============================
../../usr/local/lib/python3.12/site-packages/requests/__init__.py:113
  /usr/local/lib/python3.12/site-packages/requests/__init__.py:113: RequestsDependencyWarning: urllib3 (2.6.0) or chardet (7.5.1)/charset_normalizer (3.4.2) doesn't match a supported version!
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
108 passed, 1 warning in 0.85s
```

Additional checks: all three bundled workflow YAMLs parsed; every embedded shell run
block passed bash syntax validation. Python modules compiled successfully. These are
syntax checks, not a hosted GitHub Actions validation or proof of integration correctness.

Local environment (not a fresh installation of requirements.txt):

{
  "python": "3.12.8",
  "packages": {
    "numpy": "1.26.4",
    "pandas": "2.2.3",
    "requests": "2.32.3",
    "pytest": "8.3.5"
  }
}

The workflow targets Python 3.11 and installs the user's pinned requirements. This local
session uses the versions above. The requests dependency warning is from this sandbox;
it was not suppressed and did not fail tests. Verify CI in your GitHub environment.

Tests use deterministic broker/market fixtures to check mechanics, including buy ->
stop/target/time sell, repeated signals, partial fills and cancellation, inventory/fee
reconciliation, quote/spread checks, durable pre-order checkpoints, unknown POST outcomes,
read-only account checks, account-ID mismatch and ledger/journal rendering.

Unchanged supplied files: cryptolab.py, paper_report.py, config.json, requirements.txt,
tests/test_lab.py and .github/workflows/paper.yml. Their unchanged bytes are verified in
this build. No stock repository file is included or modified.
