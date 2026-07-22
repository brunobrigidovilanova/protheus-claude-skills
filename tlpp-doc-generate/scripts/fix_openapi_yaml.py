#!/usr/bin/env python3
"""Corrige o YAML OpenAPI gerado pelo tlpp.doc.generate() do Protheus.

Problemas corrigidos:
1. Encoding: o motor grava em CP1252; parsers/exploradores esperam UTF-8.
2. Chaves de path duplicadas: o motor emite um bloco por verbo para o mesmo
   path (ex.: get num bloco, put em outro), o que gera "duplicated mapping key"
   no js-yaml do Explorador OpenAPI. Os blocos sao mesclados sob uma unica
   chave; verbos repetidos (conteudo redundante) sao descartados com aviso.

Uso: python fix_openapi_yaml.py <entrada.yaml> [saida.yaml]
     (sem saida, grava <entrada>_fixed.yaml)
"""
import io
import re
import sys
import collections


def read_lines(path):
    for enc in ("cp1252", "utf-8-sig", "latin-1"):
        try:
            return io.open(path, encoding=enc).read().splitlines()
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"nao consegui decodificar {path}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else re.sub(r"\.ya?ml$", "", src) + "_fixed.yaml"

    lines = read_lines(src)

    # separa header (ate 'paths:'), blocos de path ('  /...:') e footer (coluna 0)
    header, i, n = [], 0, len(lines)
    while i < n and lines[i].rstrip() != "paths:":
        header.append(lines[i])
        i += 1
    if i == n:
        raise SystemExit("secao 'paths:' nao encontrada — e um YAML OpenAPI?")
    header.append(lines[i])
    i += 1

    order, bodies, cur = [], {}, None
    while i < n:
        l = lines[i]
        if re.match(r"^  /\S.*:\s*$", l):
            cur = l.strip()
            if cur not in bodies:
                order.append(cur)
                bodies[cur] = []
        elif l and not l.startswith("    ") and not l.startswith("  /") and l.strip():
            break  # fim da secao paths (ex.: components: na coluna 0)
        elif cur is not None:
            bodies[cur].append(l)
        i += 1
    footer = lines[i:]

    # mescla blocos e remove verbos repetidos dentro do mesmo path
    removed, fixed = [], header[:]
    for k in order:
        fixed.append("  " + k)
        seen, skip = set(), False
        for l in bodies[k]:
            m = re.match(r"^    (\w+):\s*$", l)
            if m:
                verb = m.group(1).lower()
                skip = verb in seen
                if skip:
                    removed.append(f"{k} -> {verb}")
                else:
                    seen.add(verb)
            if not skip:
                fixed.append(l)
    fixed += footer

    io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(fixed) + "\n")

    keys = [l.strip() for l in fixed if l.startswith("  /") and l.rstrip().endswith(":")]
    dup = [k for k, c in collections.Counter(keys).items() if c > 1]
    print(f"OK: {out}")
    print(f"paths unicos: {len(keys)} | duplicados restantes: {len(dup)}")
    if removed:
        print(f"verbos redundantes descartados ({len(removed)}):")
        for r in removed:
            print("  -", r)


if __name__ == "__main__":
    main()
