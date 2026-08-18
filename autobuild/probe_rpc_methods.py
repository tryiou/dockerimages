#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys

REQUIRED_METHODS = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'required_rpc_methods.json')


def method_supported(container, stem, method):
    proc = subprocess.run(
        ['docker', 'exec', container, '%s-cli' % stem, method],
        capture_output=True,
        text=True,
    )
    out = proc.stdout + proc.stderr
    if '-32601' in out or 'Method not found' in out:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description='Probe a running daemon for the RPC methods the Blocknet coin connector requires.')
    parser.add_argument('--container', required=True, help='Running container name, e.g. bitcoin-cash-v29.1.0-staging')
    parser.add_argument('--stem', required=True, help='Daemon executable stem, e.g. bitcoin')
    parser.add_argument('--family', default='btc', help='RPC method family from required_rpc_methods.json')
    parser.add_argument('--methods', default=REQUIRED_METHODS, help='Path to required_rpc_methods.json')
    args = parser.parse_args()

    with open(args.methods) as f:
        spec = json.load(f)

    family = spec.get(args.family)
    if not family:
        print('ERROR: family "%s" not found in %s' % (args.family, args.methods))
        sys.exit(1)

    failed = []
    optional_missing = []

    for method in family.get('required', []):
        ok = method_supported(args.container, args.stem, method)
        print('%s %s' % ('PASS' if ok else 'FAIL', method))
        if not ok:
            failed.append(method)

    for pair in family.get('either_or', []):
        results = [(m, method_supported(args.container, args.stem, m)) for m in pair]
        ok = any(ok for _, ok in results)
        status = 'PASS' if ok else 'FAIL'
        for m, supported in results:
            print('   [%s] %s' % (supported, m))
        print('%s %s (either-or)' % (status, ' | '.join(pair)))
        if not ok:
            failed.append(' OR '.join(pair))

    for method in family.get('optional', []):
        ok = method_supported(args.container, args.stem, method)
        print('%s %s (optional)' % ('PASS' if ok else 'MISSING', method))
        if not ok:
            optional_missing.append(method)

    if optional_missing:
        print('WARNING: optional methods not supported: %s' % ', '.join(optional_missing))

    if failed:
        print('ERROR: required RPC methods not supported: %s' % ', '.join(failed))
        sys.exit(1)

    print('All required RPC methods supported.')


if __name__ == '__main__':
    main()