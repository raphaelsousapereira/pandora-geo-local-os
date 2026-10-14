"""Ponto de entrada: python scripts/pandora_press_suite.py <press|inventory|discovery|console|selftest> ..."""
import json
import sys

from . import VERSION, console, discovery, inventory, press

USAGE = ('PANDORA PRESS-SUITE Ω v' + VERSION + '\n'
         'uso: pandora_press_suite.py press <comando> ... | inventory ... | discovery ... | console [--port N] | selftest')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help'):
        print(USAGE); return 0
    tool, rest = argv[0], argv[1:]
    if tool == 'selftest':
        results = {'press': press.main(['selftest']) == 0, 'inventory': inventory.selftest(), 'discovery': discovery.selftest()}
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0 if results['press'] else 1
    if tool == 'press':
        return press.main(rest)
    mains = {'inventory': inventory.main, 'discovery': discovery.main, 'console': console.main}
    if tool not in mains:
        print(USAGE, file=sys.stderr); return 2
    sys.argv = ['pandora_press_suite.py ' + tool] + rest
    return mains[tool]() or 0


if __name__ == '__main__':
    sys.exit(main())
