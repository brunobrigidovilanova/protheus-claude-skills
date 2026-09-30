---
name: mit044-especificacao
description: "Use quando o usuário pedir para criar, escrever, gerar ou atualizar uma MIT044 — gatilhos: 'MIT044', 'MIT 044', 'especificação da customização', 'documento de customização TOTVS', 'documentar o GAP', 'escrever a MIT do desenvolvimento', 'gerar o docx da customização'. Vale para qualquer cliente/projeto Protheus, não só para o cliente atual."
license: MIT
metadata:
  domain: Protheus
  author: Claude + Bruno Brigido Vilanova
  version: '1.1.0'
  category: Documentation
---

# MIT044 — Especificação da Customização

## Overview

Gera o .docx da MIT044 (documento que a TOTVS entrega ao cliente descrevendo um GAP/customização)
no layout oficial: capa de ambientação, histórico de versões, sumário, cabeçalho/rodapé com a
identidade visual, as cinco seções numeradas e o aceite. O conteúdo vem de um **JSON**; o layout
vem do **template oficial da TOTVS** embutido na skill, com os ajustes de diagramação já revisados
(caixa de texto do cabeçalho dimensionada para o título caber em uma linha, listas com recuo à
esquerda, espaçamento entre blocos).

Ao gerar o documento, o gerador ainda limpa do template os parágrafos de orientação entre `<` e
`>` e os placeholders `{{campo}}` da capa, e conserta o campo do sumário (o TOC original seleciona
os títulos por nome de estilo em inglês e não monta nada no Word em português).

Este documento é de **negócio**, não técnico: descreve o que muda para o usuário. Nomes de
função AdvPL, classes, tabelas e detalhes de implementação pertencem à especificação técnica,
não aqui.

## Quando usar / não usar

**Use quando:** for preciso formalizar uma customização para o cliente aprovar; atualizar uma
MIT044 existente; ou padronizar um documento escrito à mão.

**Não use para:** especificação técnica (dicionário, PE, fontes) — use `planejar-advpl` e
`prd-protheus`; nem para MIT041 (diagrama de processos do módulo), que tem outro layout.

## Etapa 0 — OBRIGATÓRIA: levantar antes de escrever

Nunca invente conteúdo de negócio. Antes de montar o JSON, confirme com o usuário:

1. **Título da customização** e a **tag do cliente** que abre o nome do arquivo (`[Cliente]`).
2. **Dados da capa** — se já existe uma MIT044 do mesmo projeto na pasta, leia-os de lá em vez de
   perguntar (`python -c "import docx; print(docx.Document(r'...').tables[0].rows[1].cells[0].text)"`).
3. **A fonte do conteúdo**: ata de reunião, e-mail, ticket, plano em `.claude/plans/`. Se não
   houver fonte, pergunte — não preencha com suposição.
4. O que ainda está **pendente de definição** (TES/CFOP com o fiscal, layout, volumetria). Isso
   vira texto explícito no documento ("Pendente de definição com ...") em vez de sumir.

## Fluxo

1. Copie `references/exemplo-conteudo.json` para o scratchpad e preencha com o conteúdo real.
   As regras de redação de cada seção estão em [references/guia-redacao.md](references/guia-redacao.md) — **leia antes de escrever**.
2. Gere o documento:
   ```bash
   python ~/.claude/skills/mit044-especificacao/scripts/gera_mit044.py <conteudo.json> --saida "<pasta Documentos do cliente>"
   ```
3. Valide a estrutura (compare com uma MIT044 aprovada do mesmo projeto, se houver):
   ```bash
   python ~/.claude/skills/mit044-especificacao/scripts/valida_mit044.py "<gerado.docx>" --ref "<mit044-aprovada.docx>"
   ```
4. Informe ao usuário o caminho do arquivo **e a lista de pendências manuais** (abaixo).

Opções do gerador: `--force` sobrescreve (salvando `.bak` antes) · `--template` usa outro
esqueleto · `--numeracao-uniforme` põe os cinco títulos na mesma lista numerada ·
`--sem-respiro` desliga as quebras de linha que separam os blocos.

O gerador já entrega o documento diagramado, sem os retoques que antes eram feitos à mão no Word:

- quebra de linha antes de cada rótulo em negrito, antes de cada título de seção e antes do Aceite
  (desligue com `--sem-respiro`);
- bullets e passos numerados com **recuo à esquerda** de 1 cm, para a segunda linha alinhar com a
  primeira em vez de voltar à margem;
- quebra de página antes do quadro "Dados da Customização", que assim não disputa espaço com o
  sumário na primeira página.

## Schema do JSON

| Chave | Tipo | Conteúdo |
|---|---|---|
| `arquivo.tag_cliente` / `arquivo.titulo` | texto | montam `[tag] - Especificação da Customização - MIT044 - titulo.docx` |
| `capa.*` | texto | `nome_cliente`, `codigo_cliente`, `nome_projeto`, `codigo_projeto`, `segmento_cliente`, `unidade_totvs`, `data`, `proposta_comercial`, `gerente_totvs`, `gerente_cliente`, `responsavel_totvs`, `responsavel_cliente`, `qtd_horas` |
| `capa.extra_projeto` | `sim`/`nao`/`""` | marca o checkbox correspondente |
| `capa.criticidade` | `alto`/`medio`/`baixo`/`""` | marca o checkbox de criticidade |
| `titulos_secoes` | objeto (opcional) | renomeia os cinco títulos de seção: `{"Processo Atual": "Visão Geral", …}`. Use ao documentar uma customização **já implantada**, em que "Processo Atual/Proposto" não descrevem mais nada. O sumário continua certo: o campo TOC seleciona por nível, não por nome |
| `historico` | lista (opcional) | linhas da tabela "Histórico de Versões": `{"data", "versao", "autor", "descricao"}`. Omitido, gera uma linha com a data da capa, versão `1.00`, o responsável TOTVS e "Emissão inicial do documento." |
| `processo_atual`, `processo_proposto`, `parametrizacoes` | lista | item = texto (parágrafo) ou `{"tipo": …}` — ver **Itens de conteúdo** abaixo |
| `execucao` | objeto | chaves fixas `objetivos`, `fluxo`, `premissas`, `plano_teste` (listas) e `rastreabilidade` (texto) |
| `customizacoes.periodicidade` | objeto | `sob_demanda`/`job`/`continua` (textos) + `marcada` (qual recebe o "X") |
| `customizacoes.onde_executada` | objeto | `texto`, `rotina`, `menu` |
| `customizacoes.funcionalidades` | lista | bullets no formato `RF01 — ...;` |
| `customizacoes.premissas_tecnicas`, `prototipo_tela` | lista/texto | — |
| `customizacoes.anexos` | lista de pares | `["Descrição", "Observação"]` |

Os **labels em negrito** de cada bloco ("Objetivos do negócio:", "Anexos:"…) são escritos pelo
gerador — não os coloque no JSON.

## Itens de conteúdo

Toda lista de conteúdo (`processo_atual`, `processo_proposto`, `parametrizacoes`, os
blocos de `execucao` e os de `customizacoes`) aceita, além da string solta, estes objetos:

| `tipo` | Campos | Resultado |
|---|---|---|
| `p` | `texto` | parágrafo narrativo |
| `bullet` | `texto` | bullet recuado 1 cm |
| `num` | `texto` | passo numerado (a numeração é contada por lista) |
| `label` | `texto` | rótulo em negrito que abre um sub-bloco |
| `tabela` | `linhas`, `titulo`, `larguras`, `fonte` | tabela de N colunas |
| `figura` | `arquivo`, `legenda`, `largura_cm` | imagem centralizada com legenda |

**Tabela.** `linhas` é uma lista de listas; a **primeira linha é o cabeçalho** e sai em
negrito. `larguras` é opcional, em centímetros, uma por coluna, e deve somar 16 (a mancha
da página) — omitida, as colunas ficam iguais. `titulo` vira um rótulo em negrito acima da
tabela; use quando houver duas ou mais tabelas seguidas no mesmo bloco. O layout é gravado
como fixo: sem isso o Word reajusta as colunas ao abrir e a largura calculada se perde.

```json
{"tipo": "tabela", "titulo": "Campos", "larguras": [0.9, 3.0, 1.0, 11.1],
 "linhas": [["#", "Campo", "Tipo", "Conteúdo"],
            ["01", "ZC4_ID", "C", "Número do repasse"]]}
```

**Figura.** `arquivo` é relativo à pasta do JSON. A largura é limitada à mancha da página,
então gere a imagem já nesse tamanho para não haver redução. A legenda sai em itálico,
centralizada, 8,5 pt — numere-a no texto (`Figura 1 — …`), porque o gerador não numera.

```json
{"tipo": "figura", "arquivo": "figuras/fluxo-1-ciclo.png",
 "legenda": "Figura 1 — Ciclo do repasse: o que é do usuário e o que o agendamento faz."}
```

## Fluxogramas

`scripts/fluxograma.py` traz as primitivas de desenho (`caixa`, `losango`, `seta`,
`caminho`, `rotulo`, `faixa`, `salva`) e a paleta. Não é um gerador automático: escreva,
ao lado do JSON, um script curto que descreve os diagramas daquele documento, rode-o e
referencie os PNGs pelos itens `figura`. Requer `matplotlib`.

```python
import sys, os
sys.path.insert(0, os.path.expanduser(r'~/.claude/skills/mit044-especificacao/scripts'))
from fluxograma import *

f, ax = figura(4.2)
caixa(ax, 50, 80, 50, 10, 'Usuário importa a planilha')
losango(ax, 50, 55, 44, 14, 'Validação\naprovada?')
caixa(ax, 50, 30, 50, 10, 'Grava os itens', bc=VERDE_B, fc=VERDE_F)
seta(ax, (50, 75), (50, 62)); seta(ax, (50, 48), (50, 35))
salva(f, 'fluxo-1-importacao.png')
```

**Sempre abra o PNG e olhe antes de inserir.** Rótulo de seta encostando em caixa, texto
maior que a caixa e linha de retorno cruzando outro elemento são os defeitos comuns, e
nenhum deles aparece no código — só no desenho pronto.

## Pendências manuais no Word (informe SEMPRE ao usuário)

- **Atualizar o sumário**: abrir o .docx, clicar no sumário e teclar **F9** (é campo do Word; o
  gerador não consegue calcular a paginação).
- Preencher **Qtd. Horas** e **Responsável no Cliente** quando forem definidos.
- Anotar as **revisões seguintes** no Histórico de Versões (o gerador escreve só as que vierem
  no JSON; as linhas restantes ficam em branco de propósito).
- Marcar **Extra Projeto** e **Criticidade** (podem vir prontos pelo JSON).
- Revisar com o fiscal do cliente qualquer TES/CFOP citado.

## Erros comuns

| Sintoma | Causa | Correção |
|---|---|---|
| `arquivo já existe (use --force…)` | proteção contra sobrescrita | use `--force` (gera `.bak`) ou mude o título |
| `FileNotFoundError` no caminho do .docx | nomes usam Unicode **NFD** (acentos decompostos) | localize por substring sem acento: `[f for f in os.listdir(D) if 'MIT044' in f]` |
| `seção obrigatória ausente no JSON` | falta uma das 7 chaves de topo | o gerador aborta **antes** de gravar; complete o JSON |
| Sumário sem as seções novas | campo TOC não recalculado | F9 no Word |
| "Nenhuma entrada de sumário foi encontrada" após o F9 | TOC do template seleciona por nome de estilo em inglês (`\t "Heading 1,1…"`) | já corrigido pelo gerador (`\o "1-2"`); em documento antigo, edite o campo do sumário |
| Numeração dos títulos sai "a., b., 01., 02." | herdado dos documentos originais (dois `numId`) | rode com `--numeracao-uniforme` |
| Espaço dobrado depois dos títulos | template extraído de uma MIT044 já gerada trouxe as quebras do respiro | o gerador limpa sozinho; para o asset, o extrator também |
| Acentos corrompidos no terminal | console cp1252 | os scripts já forçam UTF-8; não redirecione para arquivo sem `-Encoding utf8` |
| Colunas da tabela desalinhadas ao abrir no Word | autofit refez as larguras | já corrigido (layout fixo); confira se `larguras` soma 16 cm |
| Duas tabelas seguidas viraram uma só | o Word funde tabelas coladas | o gerador insere um parágrafo vazio entre elas; não o remova à mão |
| `figura não encontrada` | caminho relativo a outra pasta | o caminho é relativo à **pasta do JSON**, não à pasta atual |

## Estrutura da skill

```
scripts/gera_mit044.py       gerador (JSON + template -> .docx)
scripts/fluxograma.py        primitivas para desenhar os fluxogramas (PNG)
scripts/valida_mit044.py     conferência estrutural (20 verificações)
scripts/extrai_template.py   recria os assets a partir de uma MIT044 aprovada
assets/template-mit044.docx  template oficial TOTVS: capa, histórico, sumário, cabeçalho/rodapé
assets/prototipos.xml        fragmentos de formatação (parágrafo, label, bullet, 3 tabelas)
references/exemplo-conteudo.json  exemplo completo e preenchido
references/guia-redacao.md   como escrever cada seção (tom, tamanho, fórmulas)
```

Para trocar o template por outro (cliente com identidade visual diferente), regenere os assets a
partir de uma MIT044 aprovada daquele cliente — o processo está no fim do guia de redação.
