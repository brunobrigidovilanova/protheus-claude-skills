# mit044-especificacao

Gera o documento **MIT044 — Especificação da Customização** (padrão de projetos de implantação
TOTVS Protheus) em `.docx`, a partir de um arquivo JSON com o conteúdo.

O layout — capa de ambientação, histórico de versões, sumário, cabeçalho e rodapé institucionais,
as cinco seções numeradas e o quadro de aceite — vem do **template oficial da TOTVS** embutido na
skill, com a diagramação já revisada (caixa do cabeçalho dimensionada para o título caber em uma
linha, listas com recuo à esquerda, espaçamento entre blocos). Você escreve só o conteúdo; a
formatação sai idêntica todas as vezes.

> **Sobre o template:** o `.docx` incluído carrega a identidade visual dos documentos de
> especificação da TOTVS (logo, cabeçalho, rodapé de direitos reservados e fontes embutidas).
> Use-o no contexto para o qual ele existe — documentação de projetos Protheus. Se preferir
> outro layout, o próprio repositório traz o extrator para você gerar um template a partir de um
> documento seu (veja "Trocando o template").
>
> Os textos de orientação do template (entre `<` e `>`) e os placeholders `{{campo}}` da capa
> são removidos automaticamente do documento gerado, e o campo do sumário é corrigido para
> funcionar no Word em português.

## Requisitos

- Python 3.9+
- `python-docx` e `lxml`:
  ```bash
  pip install python-docx lxml
  ```
- Claude Code (a skill é ativada por ele; os scripts também rodam sozinhos na linha de comando)

## Instalação

```powershell
Copy-Item -Recurse .\mit044-especificacao "$env:USERPROFILE\.claude\skills\"
```

Reinicie o Claude Code. A skill passa a ser ativada quando você pedir para "criar a MIT044 de X".

## Uso

### Pelo Claude Code (recomendado)

Peça: *"criar a MIT044 do desenvolvimento de romaneio de carga"*. A skill vai levantar os dados
da capa, pedir a fonte do conteúdo (ata, e-mail, ticket), montar o JSON e gerar o documento.

### Direto na linha de comando

1. Copie `references/exemplo-conteudo.json` e preencha com o seu conteúdo. As regras de redação
   de cada seção estão em [`references/guia-redacao.md`](references/guia-redacao.md).
2. Gere:
   ```bash
   python scripts/gera_mit044.py meu-conteudo.json --saida "C:\caminho\Documentos"
   ```
3. Confira a estrutura (opcionalmente comparando com uma MIT044 aprovada):
   ```bash
   python scripts/valida_mit044.py "<gerado.docx>" --ref "<mit044-aprovada.docx>"
   ```

| Opção do gerador | Efeito |
|---|---|
| `--saida PASTA` | pasta de destino (padrão: atual) |
| `--force` | sobrescreve um arquivo existente, salvando `.bak` antes |
| `--template DOCX` | usa outro esqueleto |
| `--numeracao-uniforme` | põe os cinco títulos de seção na mesma lista numerada |
| `--sem-respiro` | desliga as quebras de linha que separam os blocos e as seções |

O documento já sai diagramado: respiro antes de cada rótulo em negrito, de cada título de seção e
do Aceite; bullets e passos numerados com recuo à esquerda de 1 cm (a segunda linha alinha com a
primeira); e quebra de página antes do quadro "Dados da Customização", que fica em página própria
em vez de disputar espaço com o sumário.

O nome do arquivo é montado como
`[<tag_cliente>] - Especificação da Customização - MIT044 - <título>.docx`.

## O que ainda é manual no Word

- **Atualizar o sumário**: abrir o documento, clicar no sumário e teclar **F9**. É um campo do
  Word — a paginação só existe depois que ele renderiza.
- Preencher **Qtd. Horas** e **Responsável no Cliente** quando forem definidos (ou informe no JSON).
- Anotar as revisões seguintes no **Histórico de Versões**: o gerador escreve as versões que vierem
  em `historico` no JSON (ou uma linha inicial, se a chave for omitida) e deixa as demais linhas
  em branco.
- Revisar com o fiscal do cliente qualquer TES/CFOP citado no texto.

## Trocando o template

Para adotar o layout de outro cliente ou de uma versão mais nova do documento:

```bash
python scripts/extrai_template.py "<mit044-aprovada.docx>" "<pasta-destino>"
```

O extrator descobre sozinho os parágrafos que servem de molde (narrativo, rótulo em negrito e
bullet), remove o miolo entre "Processo Atual" e "Aceite", esvazia a capa e o histórico de versões
e grava `template-mit044.docx` + `prototipos.xml`. Gere numa pasta temporária, confira a saída do script
e só então substitua os arquivos de `assets/`.

## Armadilhas conhecidas

| Sintoma | Causa | Correção |
|---|---|---|
| `arquivo já existe` | proteção contra sobrescrita | `--force` (gera `.bak`) ou mude o título |
| `FileNotFoundError` num caminho que existe | nomes de arquivo em Unicode **NFD** (acentos decompostos) | localize por substring sem acento, com `os.listdir` |
| Sumário sem as seções | campo TOC não recalculado | F9 no Word |
| "Nenhuma entrada de sumário foi encontrada" | o TOC do template seleciona os títulos por nome de estilo em inglês, que o Word em português não reconhece | o gerador já reescreve o campo como `TOC \o "1-2"`; num documento antigo, edite o campo do sumário |
| Títulos numerados como "a., b., 01., 02." | os documentos de origem usam duas listas diferentes nos títulos | `--numeracao-uniforme` |
| `seção obrigatória ausente no JSON` | falta uma das sete chaves de topo | o gerador aborta antes de gravar; complete o JSON |

## Estrutura

```
SKILL.md                          instruções para o agente
README.md                         este guia
scripts/gera_mit044.py            gerador (JSON + template -> .docx)
scripts/valida_mit044.py          conferência estrutural (20 verificações)
scripts/extrai_template.py        recria os assets a partir de uma MIT044 aprovada
assets/template-mit044.docx       template oficial TOTVS: capa, histórico, sumário, cabeçalho/rodapé
assets/prototipos.xml             moldes de formatação (parágrafo, rótulo, bullet, 3 tabelas)
references/exemplo-conteudo.json  exemplo completo e preenchido (dados fictícios)
references/guia-redacao.md        como escrever cada seção (tom, tamanho, fórmulas)
```

## Como contribuir

Sugestões, correções e melhorias são bem-vindas — principalmente de quem escreve MIT044 no dia a
dia e conhece variações de layout entre projetos.

1. **Faça um fork** do repositório e crie uma branch descritiva:
   ```bash
   git checkout -b melhoria/tabela-de-anexos-dinamica
   ```
2. **Faça a alteração.** Se mexer no gerador, rode o validador contra um documento gerado antes e
   depois:
   ```bash
   python scripts/gera_mit044.py references/exemplo-conteudo.json --saida ./saida-teste
   python scripts/valida_mit044.py "./saida-teste/<arquivo>.docx"
   ```
   As 20 verificações precisam continuar passando. Se a sua mudança altera a estrutura de
   propósito, ajuste também o `valida_mit044.py` e explique no PR.
3. **Abra o Pull Request** descrevendo:
   - o problema ou a lacuna que a mudança resolve;
   - o que muda no documento gerado (se possível, print do antes e depois no Word);
   - se alguma opção nova de linha de comando foi criada.

**O que não enviar no PR:**

- documentos, planilhas ou anexos de clientes reais;
- nomes de pessoas, códigos de projeto/cliente, propostas comerciais ou qualquer dado de
  ambiente (hosts, usuários, senhas) — o exemplo do repositório usa dados fictícios de
  propósito, mantenha assim;
- arquivos gerados (`*.docx` de saída, `*.bak`, `__pycache__/`).

Dúvida sobre o desenho antes de investir tempo? Abra uma issue descrevendo o caso — layout
divergente de projeto, seção a mais, outro tipo de MIT — que a gente conversa antes do código.

## Licença

MIT — veja o `LICENSE` na raiz do repositório.
