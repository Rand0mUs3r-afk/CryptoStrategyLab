"""Workflow entry point; installs fail-closed reconciliation before execution."""
import argparse
import alpaca_crypto as a
from alpaca_reconciliation import install


def main():
    install(a)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('check', 'plan', 'tick'), default='check')
    parser.add_argument('--state', default='state/alpaca_state.json')
    parser.add_argument('--output', default='output/alpaca')
    parser.add_argument('--execution-config', default='alpaca_config.json')
    parser.add_argument('--checkpoint-script')
    args = parser.parse_args()
    a.run(args.mode, args.state, args.output, args.execution_config, args.checkpoint_script)


if __name__ == '__main__':
    main()
