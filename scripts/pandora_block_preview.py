#!/usr/bin/env python3
"""Gera uma prévia autônoma (com <meta charset="utf-8">) de um bloco "HTML personalizado".

O bloco não declara charset porque vai dentro do tema WordPress, que já declara UTF-8.
Aberto sozinho no celular ou no navegador, ele cai em Latin-1 e os acentos quebram
("VerÃ´nica"). A prévia resolve isso sem mudar o bloco que vai para o site.

Uso: python3 scripts/pandora_block_preview.py BLOCO.html PREVIA.html "Título da aba"
"""
import html, sys
from pathlib import Path

def main(src, dst, title):
    body = Path(src).read_text(encoding='utf-8')
    page = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="robots" content="noindex">\n'
            f'<title>{html.escape(title)}</title>\n'
            '<style>body{margin:0;background:#fff}</style>\n</head>\n<body>\n<main>\n'
            + body.rstrip('\n') + '\n</main>\n</body>\n</html>\n')
    Path(dst).write_text(page, encoding='utf-8')

if __name__ == '__main__':
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(*sys.argv[1:])
