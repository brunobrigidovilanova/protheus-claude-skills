---
name: sessao
description: Grava um atalho .bat no Desktop que reabre esta janela do Claude Code exatamente onde parou (claude --resume). Use quando o usuario digitar /sessao ou pedir para salvar/gravar a sessao atual para voltar depois.
argument-hint: [nome-do-atalho]
disable-model-invocation: true
---

# Sessao — atalho .bat para retomar esta janela depois

## Objetivo

Gerar um unico arquivo `.bat` em `%USERPROFILE%\Desktop\Sessoes Claude` que, ao ser
clicado, abre o terminal **no diretorio do projeto** ja rodando `claude --resume <id>`
desta janela. O usuario fecha a sessao com `exit` e volta a ela depois com um duplo clique.

Nao confundir com `/session-summary` e `/session-resume`: aquelas geram um `.md` de resumo
para recarregar contexto apos `/clear`. Esta skill retoma a **sessao real do CLI**, com o
historico completo da conversa.

## Procedimento

### Passo 1 — Descobrir o SESSION_ID e o PROJETO_ENCODADO

O caminho do scratchpad informado no system prompt tem esta forma:

```
%LOCALAPPDATA%\Temp\claude\<PROJETO_ENCODADO>\<SESSION_ID>\scratchpad
```

- `<SESSION_ID>` = o segmento imediatamente antes de `scratchpad` (um UUID).
- `<PROJETO_ENCODADO>` = o segmento anterior a ele (ex.: `C--Users-User`).

**Fallback** (se o caminho do scratchpad nao estiver disponivel): pegue o `.jsonl` mais
recente em `%USERPROFILE%\.claude\projects\<PROJETO_ENCODADO>\` e confirme o campo
`sessionId` da primeira linha do arquivo. Outra fonte util:
`%USERPROFILE%\.claude\sessions\<pid>.json`, que traz `sessionId`, `cwd` e `name`.

Sempre valide que existe
`%USERPROFILE%\.claude\projects\<PROJETO_ENCODADO>\<SESSION_ID>.jsonl` antes de seguir.

### Passo 2 — Determinar o diretorio do projeto

E o working directory desta sessao (o `cwd` que aparece no ambiente / no transcript).
E o diretorio onde o `claude --resume` precisa rodar para achar a conversa.

### Passo 3 — Definir o assunto

Uma frase curta e **especifica** do que foi tratado na janela — o que faz o usuario
reconhecer o atalho na pasta meses depois.

- Bom: `Skill sessao com atalho bat`, `Lentidao no faturamento`, `API REST de pedidos`
- Ruim: `Sessao do dia`, `Conversa Claude`, `Duvidas`

Se `$ARGUMENTS` foi informado, use-o como assunto, sem reescrever.

### Passo 4 — Definir a cor da aba (opcional)

Se o usuario mencionar uma cor (`/sessao API de pedidos em azul`, "grava com a aba vermelha"),
passe-a em `-Cor`. Valores aceitos: `vermelho`, `verde`, `azul`, `ciano`, `amarelo`,
`roxo`, `laranja`, `rosa`, `cinza` — ou um hex `#RRGGBB`.

Se nenhuma cor for mencionada, **nao pergunte**: omita o parametro. O script mantem a cor
que o atalho ja tinha (se estiver sendo atualizado) ou deixa a aba no padrao do
Windows Terminal.

### Passo 4b — Modo de permissao (automatico)

**Nao precisa fazer nada:** o script le o ultimo `permissionMode` do transcript e grava o modo
em que a sessao estava (`auto`, `bypassPermissions`, `plan`, `default`, `manual`,
`acceptEdits`, `dontAsk`). Passe `-Modo` **so** se o usuario pedir explicitamente para o
atalho abrir em outro modo ("quero que volte em modo plano").

### Passo 5 — Gravar o atalho

Chame o script auxiliar (caminhos entre aspas):

```powershell
& "$env:USERPROFILE\.claude\skills\sessao\scripts\gravar-sessao.ps1" `
    -SessionId "<SESSION_ID>" `
    -ProjectDir "<CWD>" `
    -ProjectEncoded "<PROJETO_ENCODADO>" `
    -Assunto "<assunto>" `
    -Cor "<cor>" `        # omita a linha inteira quando nao houver cor
    -Modo "<modo>"        # omita: o modo e detectado sozinho
```

O script valida o transcript, cria a pasta se necessario, gera
`AAAA-MM-DD - <Assunto>.bat` e devolve `OK|<acao>|<caminho>`, onde `<acao>` e
`criado`, `atualizado` ou `renomeado`. Se o transcript nao existir, ele aborta com erro
e **nao** gera arquivo — nesse caso, revise o SESSION_ID em vez de insistir.

### Passo 6 — Confirmar ao usuario

Informe o caminho completo do `.bat` e a instrucao de uso em uma linha:

> **Sessao gravada:** `%USERPROFILE%\Desktop\Sessoes Claude\2026-08-13 - <assunto>.bat`
> Pode dar `exit` — para voltar a esta conversa, e so dar duplo clique nesse arquivo.

Se a acao foi `renomeado` ou `atualizado`, diga que o atalho existente desta sessao foi
reaproveitado (nao existem dois arquivos para a mesma conversa).

## Detalhes do .bat gerado

- Abre o Windows Terminal (`wt.exe -d <projeto>`) com `powershell.exe -NoExit`;
  se o Windows Terminal nao existir, cai para `powershell.exe` puro com `Set-Location`.
- Com cor definida, acrescenta `--tabColor "#RRGGBB"` — a aba do terminal volta na cor
  gravada. So funciona no Windows Terminal (o fallback classico nao tem abas).
- Acrescenta `--permission-mode <modo>` para a sessao voltar no mesmo modo de permissao.
  **Atencao:** um atalho gravado em `bypassPermissions` reabre com as permissoes ignoradas.
- Usa `%USERPROFILE%\.local\bin\claude.exe` e cai para `claude` do PATH se nao achar.
- Confere se o transcript ainda existe e avisa com mensagem clara caso tenha sido
  removido pela limpeza automatica, em vez de deixar o CLI falhar cru.
- Repassa argumentos com `%*`: rodar o atalho pela linha de comando com `--fork-session`
  abre uma copia da conversa sem alterar a original.

## Erros comuns

- **Assunto generico** — o nome do arquivo e a unica pista do que era aquela sessao.
- **Acento no corpo do .bat** — o cmd usa codepage OEM e embaralha. O script ja remove a
  acentuacao do conteudo; o **nome do arquivo** pode ter acentos normalmente.
- **Duplicar atalho** — nunca gere um segundo `.bat` para um SESSION_ID que ja tem um.
  O script cuida disso, desde que voce passe o SessionId correto.
- **Gravar o ID errado** — em maquina com varias janelas abertas no mesmo diretorio, o
  `.jsonl` mais recente pode ser de outra janela. Prefira sempre o caminho do scratchpad.
