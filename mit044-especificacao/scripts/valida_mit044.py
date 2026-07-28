# -*- coding: utf-8 -*-
"""Confere a estrutura de uma MIT044 gerada, comparando com um documento de referencia.

Uso:
    python valida_mit044.py <gerado.docx> [--ref <referencia.docx>]

Sai com codigo 1 se alguma verificacao falhar.
"""
import sys, os, re, argparse, zipfile
sys.stdout.reconfigure(encoding='utf-8')
import docx
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

ESQUELETO = [
    ('Title', 'Ambientação'),
    ('Title', 'Sumário'),
    ('Title', 'Especificação da Customização'),
    ('Heading 2', 'Processo Atual'),
    ('Heading 2', 'Processo Proposto'),
    ('Heading 2', 'Parametrizações'),
    ('Heading 2', 'Execução'),
    ('Heading 2', 'Customizações'),
    ('Heading 1', 'Aceite'),
]
LABELS = [
    'Objetivos do negócio:', 'Fluxo do processo:', 'Premissas e Restrições:',
    'Plano de teste e cenários esperados:', 'Rastreabilidade / dependência com outra MIT044:',
    'Periodicidade de execução:', 'Onde será executada:', 'Funcionalidades:',
    'Premissas e restrições técnicas:', 'Protótipo de tela:', 'Anexos:',
]
CABECALHOS_TABELA = ['', 'Dados da Customização', 'Forma de execução',
                     'Rotina (código provisório)', 'Descrição', 'Aprovado por']

falhas = []
total = [0]


def ok(cond, msg, detalhe=''):
    total[0] += 1
    print(('  OK   ' if cond else '  FALHA') + '  ' + msg + (('  -> ' + detalhe) if detalhe and not cond else ''))
    if not cond:
        falhas.append(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx')
    ap.add_argument('--ref', default=None, help='MIT044 de referência para comparação')
    args = ap.parse_args()

    doc = docx.Document(args.docx)
    print('Documento:', os.path.basename(args.docx))
    print('Tamanho  :', os.path.getsize(args.docx), 'bytes\n')

    # 1. esqueleto de titulos
    titulos = [(p.style.name, p.text.strip()) for p in doc.paragraphs
               if p.text.strip() and p.style.name in ('Title', 'Heading 1', 'Heading 2')]
    ok(titulos == ESQUELETO, 'esqueleto de títulos na ordem canônica', repr(titulos))

    # 2. tabelas
    ok(len(doc.tables) == 6, 'seis tabelas no documento', 'encontradas %d' % len(doc.tables))
    if len(doc.tables) == 6:
        cabs = [t.rows[0].cells[0].text.strip() for t in doc.tables]
        ok(cabs == CABECALHOS_TABELA, 'tabelas na ordem esperada', repr(cabs))
        ok(all(c.strip() for row in doc.tables[0].rows for c in
               [row.cells[0].text.split(':', 1)[-1]] if row.cells[0].text.strip()),
           'capa preenchida (sem rótulo órfão)')
        marc = [t for t in doc.tables[2].rows if t.cells[1].text.strip() == 'X']
        ok(len(marc) == 1, 'exatamente uma forma de execução marcada com X')

    # 3. bullets literais e labels
    textos = [p.text for p in doc.paragraphs]
    n_bullets = sum(1 for t in textos if t.startswith('•  '))
    ok(n_bullets > 0, 'bullets literais "•  " presentes', 'nenhum encontrado')
    faltando = [l for l in LABELS if l not in [t.strip() for t in textos]]
    ok(not faltando, 'todos os labels de bloco presentes', 'faltando: ' + ', '.join(faltando))

    # labels em negrito
    negrito_ok = True
    for p in doc.paragraphs:
        if p.text.strip() in LABELS and p.runs:
            if not p.runs[0].bold:
                negrito_ok = False
    ok(negrito_ok, 'labels de bloco em negrito')

    # fluxo numerado (numeração literal "1.  ", não lista do Word)
    numerados = [t for t in textos if re.match(r'^\d+\.\s\s', t.strip())]
    ok(len(numerados) >= 3, 'fluxo do processo numerado manualmente',
       '%d itens' % len(numerados))

    # 4. campo TOC
    toc = [e.text for e in doc.element.body.iter()
           if e.tag == qn('w:instrText') and e.text and 'TOC' in e.text]
    ok(bool(toc), 'campo de sumário (TOC) preservado')

    # 5. header/footer e imagens
    sec = doc.sections[0]
    ok(len(doc.sections) == 1, 'documento com uma única seção')
    z = zipfile.ZipFile(args.docx)
    midias = [n for n in z.namelist() if n.startswith('word/media/')]
    fontes = [n for n in z.namelist() if n.endswith('.odttf')]
    ok(len(midias) >= 4, 'imagens do cabeçalho/rodapé preservadas',
       '%d encontradas' % len(midias))
    ok(len(fontes) > 0, 'fontes embutidas preservadas', 'nenhuma')
    partes_hf = [n for n in z.namelist() if re.match(r'word/(header|footer)\d*\.xml', n)]
    ok(len(partes_hf) >= 2, 'partes de cabeçalho e rodapé presentes',
       'encontradas: %r' % partes_hf)

    # 6. comparacao com referencia
    if args.ref:
        ref = docx.Document(args.ref)
        t_ref = [(p.style.name, p.text.strip()) for p in ref.paragraphs
                 if p.text.strip() and p.style.name in ('Title', 'Heading 1', 'Heading 2')]
        ok(titulos == t_ref, 'esqueleto idêntico ao da MIT044 de referência')
        ok(len(doc.tables) == len(ref.tables), 'mesmo número de tabelas da referência')
        est_ref = {t.style.name if t.style else None for t in ref.tables}
        est_ger = {t.style.name if t.style else None for t in doc.tables}
        ok(est_ger == est_ref, 'mesmos estilos de tabela da referência',
           '%r vs %r' % (est_ger, est_ref))

    if falhas:
        print('\n%d de %d verificações falharam: %s'
              % (len(falhas), total[0], '; '.join(falhas)))
    else:
        print('\nTUDO OK — %d verificações' % total[0])
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
