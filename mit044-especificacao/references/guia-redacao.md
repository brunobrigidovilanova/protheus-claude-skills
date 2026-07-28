# Guia de redação da MIT044

Regras extraídas de MIT044 já aprovadas em projetos de implantação Protheus.

## Voz e vocabulário

- **Português do Brasil, impessoal e no futuro** para o que será construído ("será construída",
  "o sistema apresenta", "serão avaliados"). Nunca primeira pessoa ("faremos", "decidimos").
- **Linguagem de negócio.** O leitor é o usuário-chave do cliente, não o programador. Não cite
  nomes de função (`MaLibDoFat`), classes, variáveis, tabelas (`SC6`), `Begin Transaction`,
  índices ou padrões de projeto. O que o cliente reconhece **pode** e **deve** aparecer:
  parâmetros (`MV_CONTERC`), CFOP (5.124/6.124), módulos (SIGAFAT), nomes de rotina padrão
  quando são o caminho de tela (Configurador, cadastro de clientes).
- **Acentuação correta** — o documento é lido por gente, não pelo AppServer.
- Bullets terminam em `;` e o último da lista em `.`.
- Quando algo ainda não está decidido, escreva-o explicitamente ("Pendente de definição com o
  fiscal do cliente", "será detalhado na especificação técnica") em vez de omitir.

## Seção a seção

### Processo Atual (3 a 5 parágrafos)
Descreve **a dor**, no presente, sem citar a solução. Estrutura que funciona:
1. como o processo funciona hoje, com as áreas envolvidas e o porquê histórico, se houver;
2. os controles manuais/paralelos (planilha, conferência a caneta, cálculo fora do sistema);
3. a consequência: retrabalho, risco de erro, falta de rastreabilidade, informação perdida.

Se a customização se apoia em outra MIT, feche o bloco apontando isso.

### Processo Proposto (3 a 4 parágrafos)
Começa com a fórmula consagrada: **"Com a entrada em operação do Protheus, ..."**. Descreve o
que passa a existir, na ordem em que o usuário vive o processo, e termina pelas regras que
variam por cliente/parâmetro. Sem detalhe de implementação.

### Parametrizações
Parágrafo de abertura fixo:
> O correto funcionamento da rotina depende das seguintes configurações e premissas sistêmicas:

Depois, bullets de **pré-requisito** (cadastros, TES, parâmetros, séries, estruturas). Fechar com:
> Serão avaliados, na especificação técnica, eventuais parâmetros próprios da rotina (SX6) para
> valores padrão de série, TES e regras de filial.

### Execução — cinco blocos na ordem fixa
| Bloco | Formato | Como escrever |
|---|---|---|
| Objetivos do negócio | 4 bullets | verbo no infinitivo: Automatizar, Garantir, Eliminar, Reduzir, Respeitar |
| Fluxo do processo | 6 a 8 passos numerados | cada passo começa com "O usuário…" ou "O sistema…", na ordem cronológica |
| Premissas e Restrições | 5 a 8 bullets | regras que limitam o escopo e o que acontece quando são violadas |
| Plano de teste e cenários esperados | 6 a 8 bullets | sempre `cenário → resultado esperado`, incluindo casos de erro e um de regressão |
| Rastreabilidade / dependência com outra MIT044 | 1 parágrafo | cite as MIT041/MIT044 relacionadas e o que cada uma fornece |

### Customizações — seis blocos na ordem fixa
- **Periodicidade de execução**: marque só uma linha da tabela. Descreva a forma escolhida entre
  parênteses ("Execução sob demanda (o usuário executa o processamento pela tela)").
- **Onde será executada**: 1 parágrafo (menu/módulo) + tabela com a rotina e a descrição de menu.
  Enquanto o fonte não tem nome, use "A definir (padrão <cliente> – <módulo>)".
- **Funcionalidades**: bullets `RF01 — ...;` numerados sem pular. Cada RF é uma capacidade
  observável pelo usuário, não uma tarefa de desenvolvimento.
- **Premissas e restrições técnicas**: aqui cabe o vocabulário semi-técnico (reutilização de
  rotinas padrão, transação única, criação de campo via Configurador), mas ainda sem código.
- **Protótipo de tela**: 1 parágrafo descrevendo painéis, grade, colunas e ações; termine com
  "O protótipo definitivo (layout e colunas) será detalhado na especificação técnica."
- **Anexos**: pares descrição/observação. Use a observação para marcar o que está pendente de
  envio pelo cliente.

## Tamanho de referência
As MIT044 aprovadas têm ~90 parágrafos de conteúdo e 6 tabelas. Documento muito mais curto
costuma indicar seção vazia; muito mais longo costuma indicar que entrou detalhe técnico.

## Regerar os assets para outro cliente

O template e os protótipos vêm de uma MIT044 real. Para adotar a identidade visual de outro
cliente, rode o extrator apontando para uma MIT044 aprovada daquele cliente:

```bash
python ~/.claude/skills/mit044-especificacao/scripts/extrai_template.py \
       "<mit044-aprovada.docx>" "<pasta de destino dos assets>"
```

Ele faz, nesta ordem: extrai os protótipos (parágrafo narrativo, label em negrito, bullet e as
três tabelas de conteúdo, localizadas pelo texto da primeira célula); remove todos os parágrafos
**e tabelas** entre "Processo Atual" e "Aceite", preservando os cinco `Heading 2`; esvazia os
valores da capa mantendo os rótulos (cada célula tem 2 runs: rótulo + valor); e grava
`template-mit044.docx` + `prototipos.xml`.

Os três parágrafos-protótipo são detectados sozinhos (o primeiro parágrafo narrativo longo, o
primeiro rótulo em negrito terminado em `:` e o primeiro bullet). O script imprime qual escolheu;
se a escolha for ruim, aponte outro parágrafo por prefixo de texto:

```bash
python ... extrai_template.py "<origem.docx>" "<destino>" --proto-body "O processo de"
```

Gere em uma pasta temporária primeiro, confira a saída do próprio script (protótipos escolhidos,
esqueleto, tabelas restantes, campo TOC) e só então substitua os arquivos em `assets/`.

Cuidado: documentos antigos podem usar o id de estilo `normal` em minúsculas, o que os quebra
como doadores de formatação — prefira sempre a MIT044 mais recente e visualmente correta.
