# -*- coding: utf-8 -*-
"""Gera um documento MIT044 - Especificacao da Customizacao (padrao TOTVS) em .docx
a partir de um JSON de conteudo, usando o template e os prototipos de formatacao
da skill mit044-especificacao.

Uso:
    python gera_mit044.py <conteudo.json> [--saida PASTA] [--template DOCX] [--force]

O nome do arquivo de saida e montado como:
    [<tag_cliente>] - Especificacao da Customizacao - MIT044 - <titulo>.docx
"""
import sys, os, json, copy, shutil, argparse
sys.stdout.reconfigure(encoding='utf-8')
import docx
from docx.oxml.ns import qn
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from lxml import etree

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(AQUI, '..', 'assets'))
TEMPLATE_PADRAO = os.path.join(ASSETS, 'template-mit044.docx')
PROTOTIPOS = os.path.join(ASSETS, 'prototipos.xml')

W_P, W_TBL, W_R, W_T = qn('w:p'), qn('w:tbl'), qn('w:r'), qn('w:t')
BULLET = '•  '          # bullet literal + 2 espacos (padrao dos documentos)
VAZIO, MARCADO = '☐', '☒'

SECOES = ['Processo Atual', 'Processo Proposto', 'Parametrizações', 'Execução', 'Customizações']

# rotulo na tabela de capa -> chave no JSON
CAPA = [
    ('Nome do cliente',            'nome_cliente'),
    ('Código de cliente',          'codigo_cliente'),
    ('Nome do projeto',            'nome_projeto'),
    ('Código do projeto',          'codigo_projeto'),
    ('Segmento cliente',           'segmento_cliente'),
    ('Unidade TOTVS',              'unidade_totvs'),
    ('Data',                       'data'),
    ('Proposta comercial',         'proposta_comercial'),
    ('Gerente/Coordenador TOTVS',  'gerente_totvs'),
    ('Gerente/Coordenador cliente', 'gerente_cliente'),
]
DADOS_CUST = [
    ('Qtd. Horas',            'qtd_horas'),
    ('Responsável no Cliente', 'responsavel_cliente'),
    ('Responsável na TOTVS',  'responsavel_totvs'),
]
CRITICIDADE = {'alto': 'Alto Impacto', 'medio': 'Médio Impacto', 'baixo': 'Baixo Impacto'}

# labels fixos dos blocos, na ordem em que aparecem no documento
BLOCOS_EXECUCAO = [
    ('objetivos',       'Objetivos do negócio:',    'bullet'),
    ('fluxo',           'Fluxo do processo:',       'num'),
    ('premissas',       'Premissas e Restrições:',  'bullet'),
    ('plano_teste',     'Plano de teste e cenários esperados:', 'bullet'),
    ('rastreabilidade', 'Rastreabilidade / dependência com outra MIT044:', 'p'),
]
LABELS_CUSTOMIZACOES = [
    'Periodicidade de execução:', 'Onde será executada:', 'Funcionalidades:',
    'Premissas e restrições técnicas:', 'Protótipo de tela:', 'Anexos:',
]
TODOS_LABELS = {l for _, l, _ in BLOCOS_EXECUCAO} | set(LABELS_CUSTOMIZACOES)


class ErroConteudo(Exception):
    pass


# ------------------------------------------------------------------ prototipos
def carrega_prototipos():
    if not os.path.isfile(PROTOTIPOS):
        raise ErroConteudo('prototipos.xml não encontrado em ' + ASSETS)
    root = etree.parse(PROTOTIPOS).getroot()
    return {p.get('id'): p[0] for p in root}


def clona_paragrafo(proto, texto):
    """Clona um <w:p> protótipo trocando o texto e preservando pPr/rPr."""
    p = copy.deepcopy(proto)
    for tag in ('w:hyperlink', 'w:bookmarkStart', 'w:bookmarkEnd', 'w:proofErr'):
        for el in p.findall(qn(tag)):
            p.remove(el)
    runs = p.findall(W_R)
    if not runs:
        raise ErroConteudo('protótipo de parágrafo sem run')
    primeiro = runs[0]
    for r in runs[1:]:
        p.remove(r)
    ts = primeiro.findall(W_T)
    for t in ts[1:]:
        primeiro.remove(t)
    if not ts:
        t = etree.SubElement(primeiro, W_T)
        ts = [t]
    ts[0].text = texto
    ts[0].set(qn('xml:space'), 'preserve')
    return p


def texto_celula(tc, texto, doc):
    """Escreve texto em uma celula de tabela preservando a formatacao do 1o run."""
    cell = _Cell(tc, doc)
    ps = tc.findall(W_P)
    for extra in ps[1:]:
        tc.remove(extra)
    p = ps[0]
    runs = p.findall(W_R)
    if not runs:
        r = etree.SubElement(p, W_R)
        runs = [r]
    primeiro = runs[0]
    for r in runs[1:]:
        p.remove(r)
    ts = primeiro.findall(W_T)
    for t in ts[1:]:
        primeiro.remove(t)
    if not ts:
        t = etree.SubElement(primeiro, W_T)
        ts = [t]
    ts[0].text = texto
    ts[0].set(qn('xml:space'), 'preserve')


def clona_tabela(proto, linhas, doc):
    """Clona a tabela protótipo ajustando o número de linhas e o conteúdo."""
    tbl = copy.deepcopy(proto)
    trs = tbl.findall(qn('w:tr'))
    if len(linhas) > len(trs):
        modelo = copy.deepcopy(trs[-1])
        for _ in range(len(linhas) - len(trs)):
            tbl.append(copy.deepcopy(modelo))
        trs = tbl.findall(qn('w:tr'))
    for tr in trs[len(linhas):]:
        tbl.remove(tr)
    trs = tbl.findall(qn('w:tr'))
    for tr, linha in zip(trs, linhas):
        tcs = tr.findall(qn('w:tc'))
        for tc, txt in zip(tcs, linha):
            texto_celula(tc, txt, doc)
    return tbl


# ------------------------------------------------------------------ documento
def acha_headings(doc):
    heads = {}
    for el in doc.element.body.iterchildren():
        if el.tag == W_P:
            p = Paragraph(el, doc)
            txt = p.text.strip()
            if p.style.name in ('Heading 1', 'Heading 2') and txt in SECOES + ['Aceite']:
                heads[txt] = el
    faltando = [s for s in SECOES + ['Aceite'] if s not in heads]
    if faltando:
        raise ErroConteudo('template sem os headings: ' + ', '.join(faltando))
    return heads


def limpa_miolo(doc, heads):
    """Remove parágrafos E tabelas entre 'Processo Atual' e 'Aceite' (idempotência)."""
    body = doc.element.body
    manter = {id(heads[s]) for s in SECOES}
    dentro, removidos = False, 0
    for el in list(body.iterchildren()):
        if el is heads['Processo Atual']:
            dentro = True
            continue
        if el is heads['Aceite']:
            break
        if dentro and id(el) not in manter:
            body.remove(el)
            removidos += 1
    return removidos


def uniformiza_numeracao(doc, heads):
    """Poe os 5 Heading 2 na MESMA lista numerada.

    Nos documentos de origem, 'Processo Atual' e 'Processo Proposto' costumam usar
    numId=1/ilvl=1 e os tres seguintes numId=5/ilvl=0 — a numeracao sai quebrada
    (a., b., 01., 02., 03.). Só é aplicado com --numeracao-uniforme.
    """
    ref = heads['Parametrizações'].find(qn('w:pPr')).find(qn('w:numPr'))
    if ref is None:
        return 0
    trocados = 0
    for nome in SECOES:
        pPr = heads[nome].find(qn('w:pPr'))
        atual = pPr.find(qn('w:numPr'))
        if atual is not None:
            pPr.remove(atual)
        novo = copy.deepcopy(ref)
        # no OOXML o numPr vem logo depois do pStyle dentro do pPr
        pStyle = pPr.find(qn('w:pStyle'))
        if pStyle is not None:
            pStyle.addnext(novo)
        else:
            pPr.insert(0, novo)
        trocados += 1
    return trocados


def preenche_capa(doc, capa):
    tab = doc.tables[0]
    achados = set()
    for row in tab.rows:
        for tc in row._tr.tc_lst:
            cell = _Cell(tc, tab)
            txt = cell.text.strip()
            for rotulo, chave in CAPA:
                if txt.startswith(rotulo + ':') and chave not in achados:
                    escreve_valor(cell, rotulo, capa.get(chave, ''))
                    achados.add(chave)
                    break
    faltou = [c for _, c in CAPA if c not in achados]
    if faltou:
        print('  aviso: rótulos não localizados na capa: ' + ', '.join(faltou))

    # tabela "Dados da Customizacao"
    dados = doc.tables[1]
    for row in dados.rows:
        cell = row.cells[0]
        txt = cell.text.strip()
        for rotulo, chave in DADOS_CUST:
            if txt.startswith(rotulo):
                escreve_valor(cell, rotulo, capa.get(chave, ''))
                break
        if txt.startswith('Extra Projeto'):
            marca_checkbox(cell, {'sim': 'Sim', 'nao': 'Não'}.get(
                str(capa.get('extra_projeto', '')).lower(), ''))
        if txt.startswith('Criticidade'):
            marca_checkbox(cell, CRITICIDADE.get(
                str(capa.get('criticidade', '')).lower(), ''))


def escreve_valor(cell, rotulo, valor):
    """Troca só o valor, preservando o run do rótulo (que costuma estar em negrito)."""
    valor = '' if valor is None else str(valor)
    for p in cell.paragraphs:
        runs = p.runs
        if not runs:
            continue
        if len(runs) >= 2:
            # o run do rótulo às vezes já termina com espaço — não duplicar
            separador = '' if runs[0].text.endswith((' ', '\t')) else ' '
            runs[1].text = (separador + valor) if valor else ''
            for r in runs[2:]:
                r.text = ''
        else:
            runs[0].text = rotulo + ': ' + valor
        return


def marca_checkbox(cell, alvo):
    """Troca ☐ por ☒ na opção escolhida (alvo = texto que segue o checkbox)."""
    if not alvo:
        return
    for p in cell.paragraphs:
        for r in p.runs:
            if VAZIO in r.text and alvo in r.text:
                partes = r.text.split(VAZIO)
                novo = partes[0]
                for trecho in partes[1:]:
                    marca = MARCADO if trecho.lstrip().startswith(alvo) else VAZIO
                    novo += marca + trecho
                r.text = novo


def respiro(p_el, onde='fim'):
    """Insere uma quebra de linha (<w:br>, o Shift+Enter do Word) para separar blocos.

    Clona o primeiro run do parágrafo para herdar a formatação e troca o texto pela
    quebra. É assim que a separação entre blocos aparece nas MIT044 revisadas à mão.
    """
    if p_el is None or p_el.tag != W_P:
        return p_el
    runs = p_el.findall(W_R)
    if not runs:
        return p_el
    novo = copy.deepcopy(runs[0])
    for t in novo.findall(W_T):
        novo.remove(t)
    for br in novo.findall(qn('w:br')):
        novo.remove(br)
    etree.SubElement(novo, qn('w:br'))
    if onde == 'fim':
        runs[-1].addnext(novo)
    else:
        runs[0].addprevious(novo)
    return p_el


def aplica_respiro(elementos):
    """Separa visualmente os blocos: a quebra vai no fim do elemento anterior; quando
    o anterior é uma tabela (onde não cabe <w:br>), vai no início do próprio label."""
    for i, el in enumerate(elementos):
        if i == 0 or el.tag != W_P:
            continue
        if ''.join(el.itertext()).strip() not in TODOS_LABELS:
            continue
        anterior = elementos[i - 1]
        if anterior.tag == W_TBL:
            respiro(el, 'inicio')
        else:
            respiro(anterior, 'fim')
    return elementos


def insere_apos(ancora, elementos):
    cur = ancora
    for el in elementos:
        cur.addnext(el)
        cur = el
    return cur


# ------------------------------------------------------------------ conteudo
def itens_para_elementos(itens, protos, contexto):
    """Converte a lista do JSON em elementos <w:p>. Item pode ser string (parágrafo)
    ou objeto {"tipo": "p"|"bullet"|"num"|"label", "texto": "..."}."""
    out = []
    n_num = 0
    for item in itens:
        if isinstance(item, str):
            tipo, texto = 'p', item
        elif isinstance(item, dict):
            tipo, texto = item.get('tipo', 'p'), item.get('texto', '')
        else:
            raise ErroConteudo('item inválido em %s: %r' % (contexto, item))
        if not texto:
            raise ErroConteudo('item sem texto em ' + contexto)
        if tipo == 'bullet':
            out.append(clona_paragrafo(protos['bullet'], BULLET + texto))
        elif tipo == 'num':
            n_num += 1
            out.append(clona_paragrafo(protos['bullet'], '%d.  %s' % (n_num, texto)))
        elif tipo == 'label':
            out.append(clona_paragrafo(protos['label'], texto))
        elif tipo == 'p':
            out.append(clona_paragrafo(protos['body'], texto))
        else:
            raise ErroConteudo('tipo desconhecido "%s" em %s' % (tipo, contexto))
    return out


def bloco(protos, label, itens, formato, contexto):
    """Label em negrito + itens no formato indicado (bullet/num/p)."""
    els = [clona_paragrafo(protos['label'], label)]
    if isinstance(itens, str):
        itens = [itens]
    els += itens_para_elementos(
        [{'tipo': formato, 'texto': i} if isinstance(i, str) else i for i in itens],
        protos, contexto)
    return els


def monta_execucao(doc, protos, exe):
    els = []
    for chave, label, formato in BLOCOS_EXECUCAO:
        if chave not in exe:
            raise ErroConteudo('execucao."%s" ausente no JSON' % chave)
        els += bloco(protos, label, exe[chave], formato, 'execucao.' + chave)
    return els


def monta_customizacoes(doc, protos, cus):
    for obrig in ('periodicidade', 'onde_executada', 'funcionalidades',
                  'premissas_tecnicas', 'prototipo_tela', 'anexos'):
        if obrig not in cus:
            raise ErroConteudo('customizacoes."%s" ausente no JSON' % obrig)
    els = []

    # Periodicidade de execucao + tabela 4x2
    per = cus['periodicidade']
    marcada = per.get('marcada', 'sob_demanda')
    linhas = [['Forma de execução', 'Marcação']]
    for chave, padrao in (('sob_demanda', 'Execução sob demanda'),
                          ('job', 'Job / processamento agendado'),
                          ('continua', 'Execução contínua')):
        linhas.append([per.get(chave, padrao), 'X' if marcada == chave else ''])
    els.append(clona_paragrafo(protos['label'], 'Periodicidade de execução:'))
    els.append(clona_tabela(protos['periodicidade'], linhas, doc))

    # Onde sera executada + tabela 2x2
    onde = cus['onde_executada']
    els.append(clona_paragrafo(protos['label'], 'Onde será executada:'))
    els.append(clona_paragrafo(protos['body'], onde.get('texto', '')))
    els.append(clona_tabela(protos['rotina'], [
        ['Rotina (código provisório)', 'Descrição de menu'],
        [onde.get('rotina', 'A definir'), onde.get('menu', '')],
    ], doc))

    els += bloco(protos, 'Funcionalidades:', cus['funcionalidades'], 'bullet',
                 'customizacoes.funcionalidades')
    els += bloco(protos, 'Premissas e restrições técnicas:', cus['premissas_tecnicas'],
                 'bullet', 'customizacoes.premissas_tecnicas')
    els += bloco(protos, 'Protótipo de tela:', cus['prototipo_tela'], 'p',
                 'customizacoes.prototipo_tela')

    # Anexos + tabela
    linhas = [['Descrição', 'Observação']]
    for linha in cus['anexos']:
        if not isinstance(linha, (list, tuple)) or len(linha) != 2:
            raise ErroConteudo('cada anexo deve ser um par [descrição, observação]')
        linhas.append(list(linha))
    els.append(clona_paragrafo(protos['label'], 'Anexos:'))
    els.append(clona_tabela(protos['anexos'], linhas, doc))
    return els


# ------------------------------------------------------------------ principal
def valida(conteudo):
    for chave in ('arquivo', 'capa', 'processo_atual', 'processo_proposto',
                  'parametrizacoes', 'execucao', 'customizacoes'):
        if chave not in conteudo:
            raise ErroConteudo('seção obrigatória ausente no JSON: ' + chave)
    arq = conteudo['arquivo']
    for chave in ('tag_cliente', 'titulo'):
        if not arq.get(chave):
            raise ErroConteudo('arquivo."%s" é obrigatório' % chave)
    for chave in ('nome_cliente', 'data'):
        if not conteudo['capa'].get(chave):
            raise ErroConteudo('capa."%s" é obrigatório' % chave)


def nome_saida(arq):
    titulo = arq['titulo'].strip()
    return '[%s] - Especificação da Customização - MIT044 - %s.docx' % (
        arq['tag_cliente'].strip(), titulo)


def main():
    ap = argparse.ArgumentParser(description='Gera MIT044 (.docx) a partir de um JSON.')
    ap.add_argument('json', help='arquivo JSON com o conteúdo')
    ap.add_argument('--saida', default='.', help='pasta de destino (padrão: atual)')
    ap.add_argument('--template', default=TEMPLATE_PADRAO, help='template .docx alternativo')
    ap.add_argument('--force', action='store_true',
                    help='sobrescreve o destino (gera .bak antes)')
    ap.add_argument('--sem-respiro', action='store_true',
                    help='não insere as quebras de linha que separam os blocos')
    ap.add_argument('--numeracao-uniforme', action='store_true',
                    help='põe os 5 títulos de seção na mesma lista numerada '
                         '(corrige a numeração quebrada herdada dos documentos originais)')
    args = ap.parse_args()

    with open(args.json, encoding='utf-8') as fh:
        conteudo = json.load(fh)
    valida(conteudo)

    if not os.path.isfile(args.template):
        raise SystemExit('template não encontrado: ' + args.template)

    destino = os.path.join(os.path.abspath(args.saida), nome_saida(conteudo['arquivo']))
    if os.path.exists(destino):
        if not args.force:
            raise SystemExit('arquivo já existe (use --force para sobrescrever):\n  ' + destino)
        shutil.copy2(destino, destino + '.bak')
        print('backup:', destino + '.bak')

    protos = carrega_prototipos()
    doc = docx.Document(args.template)
    heads = acha_headings(doc)
    removidos = limpa_miolo(doc, heads)
    if removidos:
        print('miolo do template limpo: %d elementos' % removidos)

    if args.numeracao_uniforme:
        print('numeração dos títulos uniformizada: %d seções'
              % uniformiza_numeracao(doc, heads))

    preenche_capa(doc, conteudo['capa'])

    insere_apos(heads['Processo Atual'],
                itens_para_elementos(conteudo['processo_atual'], protos, 'processo_atual'))
    insere_apos(heads['Processo Proposto'],
                itens_para_elementos(conteudo['processo_proposto'], protos, 'processo_proposto'))
    insere_apos(heads['Parametrizações'],
                itens_para_elementos(conteudo['parametrizacoes'], protos, 'parametrizacoes'))
    els_exe = monta_execucao(doc, protos, conteudo['execucao'])
    els_cus = monta_customizacoes(doc, protos, conteudo['customizacoes'])
    if not args.sem_respiro:
        aplica_respiro(els_exe)
        aplica_respiro(els_cus)
        # respiro depois do título da seção e antes do Aceite (precedido de tabela)
        respiro(heads['Execução'], 'fim')
        respiro(heads['Customizações'], 'fim')
        respiro(heads['Aceite'], 'inicio')
    insere_apos(heads['Execução'], els_exe)
    insere_apos(heads['Customizações'], els_cus)

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    doc.save(destino)
    print('gerado:', destino)
    print('LEMBRETE: abra no Word e atualize o sumário (clique no sumário e tecle F9).')


if __name__ == '__main__':
    try:
        main()
    except ErroConteudo as e:
        raise SystemExit('ERRO de conteúdo: %s' % e)
