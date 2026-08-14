# sessao-retorno — atalho `.bat` para voltar à janela do Claude Code que você fechou

Grava um arquivo `.bat` no Desktop que **reabre uma sessão específica do Claude Code**, no
diretório certo, com o histórico inteiro da conversa — restaurando também a **cor da aba** do
Windows Terminal e o **modo de permissão** em que a sessão estava.

Você digita `/sessao-retorno`, dá `exit` sem medo e volta com um duplo clique.

> **Não confunda com `/session-summary` + `/session-resume`.** Aquelas geram um `.md` de resumo
> para recarregar contexto depois de um `/clear`. Esta skill não resume nada: ela retoma a
> **sessão real do CLI** (`claude --resume <id>`), com a conversa completa.
>
> Também não é `/compact`: a compactação encolhe o contexto ativo *dentro* da sessão. O `.bat`
> continua funcionando normalmente numa sessão que já foi compactada.

## Requisitos

- **Windows** — a skill gera `.bat` e usa o Windows Terminal (`wt.exe`). Há fallback para
  `powershell.exe`, mas sem Windows Terminal a cor da aba não se aplica (o console clássico não
  tem abas).
- **Claude Code** instalado e no PATH (ou em `%USERPROFILE%\.local\bin\claude.exe`).
- Windows PowerShell 5.1 — o que já vem no Windows. Não precisa de PowerShell 7.

Não depende de Protheus, TOTVS ou qualquer ferramenta de ERP: serve para qualquer projeto em que
você use o Claude Code.

## Instalação

```powershell
Copy-Item -Recurse .\sessao-retorno "$env:USERPROFILE\.claude\skills\"
```

Reinicie o Claude Code — skills são carregadas na abertura da sessão, então o comando `/sessao-retorno`
aparece a partir da **próxima** janela.

### Recomendado: aumentar a retenção dos transcripts

Por padrão o Claude Code apaga o histórico de sessões com mais de **30 dias**, e um atalho cuja
conversa foi apagada vira um arquivo morto. Para que os atalhos durem, acrescente ao
`%USERPROFILE%\.claude\settings.json`:

```json
{
  "cleanupPeriodDays": 365
}
```

O `.bat` gerado confere se o transcript ainda existe e avisa com uma mensagem clara quando ele
sumiu — em vez de deixar o CLI falhar sem explicação.

## Uso

Na janela que você quer poder retomar depois:

```
/sessao-retorno
```

O assunto é inferido da conversa. Para nomear você mesmo:

```
/sessao-retorno API de pedidos
```

Para gravar com uma cor de aba:

```
/sessao-retorno API de pedidos em azul
```

O resultado é um arquivo em `%USERPROFILE%\Desktop\Sessoes Claude`:

```
Sessoes Claude\
  2026-08-14 - API de pedidos.bat
  2026-08-13 - Refatoracao do modulo fiscal.bat
```

Duplo clique reabre a conversa. Chamando pela linha de comando, argumentos extras são repassados
ao `claude` — então `"2026-08-14 - API de pedidos.bat" --fork-session` abre uma **cópia** da
conversa sem alterar a original.

## O que o `.bat` faz ao abrir

| Passo | Por que existe |
|---|---|
| Confere se o transcript ainda existe | Avisa com mensagem clara em vez de deixar o CLI falhar cru |
| Resolve `%USERPROFILE%\.local\bin\claude.exe` | Com fallback para o `claude` do PATH |
| Abre `wt.exe -d "<projeto>"` | Windows Terminal já no diretório certo — com fallback para `powershell.exe` puro |
| Acrescenta `--tabColor "#RRGGBB"` | A aba volta na cor gravada (só no Windows Terminal) |
| Acrescenta `--permission-mode <modo>` | A sessão reabre no mesmo modo de permissão |
| Usa `-NoExit` | Se o `claude` sair com erro, a janela não fecha levando a mensagem junto |
| Repassa `%*` | Permite `--fork-session` e outras flags na chamada por linha de comando |

## A cor da aba

**Precisa ser dita na hora de gravar.** Quando você pinta a aba pela interface do Windows
Terminal (botão direito na aba → **Cor…**), a escolha não fica salva em lugar nenhum — nem no
`settings.json` do terminal, nem no registro do console. O script não tem como descobrir sozinho.

| Nome | Hex | | Nome | Hex |
|---|---|---|---|---|
| `vermelho` | `#C50F1F` | | `roxo` | `#881798` |
| `verde` | `#13A10E` | | `laranja` | `#FF8C00` |
| `azul` | `#0037DA` | | `rosa` | `#E74856` |
| `ciano` | `#3A96DD` | | `cinza` | `#767676` |
| `amarelo` | `#C19C00` | | | |

Os nomes usam a paleta **Campbell**, a mesma do tema padrão do Windows Terminal. Um hex
`#RRGGBB` avulso também vale. Nome desconhecido aborta e lista os válidos, sem tocar no atalho
existente.

**A cor gruda:** rodar `/sessao-retorno` de novo *sem* mencionar cor preserva a que o atalho já tinha —
o script lê o `--tabColor` do arquivo antigo antes de regravar.

## O modo de permissão

Esse você **não precisa informar**. Diferente da cor, o modo fica gravado no transcript: cada
mensagem carrega um campo `permissionMode`. O script lê a última ocorrência — o modo em que a
sessão estava quando você parou — e devolve no `--permission-mode`.

| Modo | O que significa ao reabrir |
|---|---|
| `auto` | Auto mode on |
| `bypassPermissions` | Bypass permissions on — **abre com as permissões ignoradas** |
| `plan` | Plan mode — volta planejando, sem editar nada |
| `default` / `manual` / `acceptEdits` / `dontAsk` | Demais modos aceitos pelo CLI |

A leitura pega só os últimos 512 KB do arquivo, porque transcripts passam de 10 MB com facilidade
— num de 11,6 MB, 77 ms.

> ⚠️ Um atalho gravado enquanto a sessão estava em `bypassPermissions` **reabre nesse modo**. Se
> o seu `settings.json` tem `skipDangerousModePermissionPrompt`, ele nem pergunta. O cabeçalho do
> `.bat` mostra a linha `REM  Modo....:` — vale saber o que cada arquivo da pasta carrega.

É uma foto do momento da gravação: se você trocar de modo **depois** de rodar `/sessao-retorno`, rode de
novo antes de sair.

## Um `.bat` por sessão

O script localiza o atalho pelo `SESSION_ID` gravado dentro dele. Rodar `/sessao-retorno` de novo na
mesma janela **renomeia ou atualiza** o arquivo existente — nunca cria um segundo `.bat` para a
mesma conversa. Se o assunto mudou, o arquivo é renomeado.

## Chamando o script direto

A skill é só a camada que descobre o ID da sessão e o assunto; o arquivo é escrito por um script
que roda sozinho:

```powershell
& "$env:USERPROFILE\.claude\skills\sessao-retorno\scripts\gravar-sessao.ps1" `
    -SessionId "00000000-1111-2222-3333-444444444444" `
    -ProjectDir "C:\Projetos\MinhaApp" `
    -ProjectEncoded "C--Projetos-MinhaApp" `
    -Assunto "Refatoracao do modulo de pedidos" `
    -Cor azul
```

Parâmetros opcionais: `-Cor`, `-Modo` (detectado sozinho quando omitido) e `-Pasta` (destino,
por padrão `%USERPROFILE%\Desktop\Sessoes Claude`). A saída é
`OK|<criado|atualizado|renomeado>|<caminho>`.

O `<PROJETO_ENCODADO>` é o nome da pasta que o Claude Code usa em
`%USERPROFILE%\.claude\projects\` — o caminho do projeto com os separadores trocados por hífen
(`C:\Projetos\MinhaApp` → `C--Projetos-MinhaApp`).

## Armadilhas conhecidas

| Sintoma | Causa | Correção |
|---|---|---|
| `Transcript nao encontrado` | `SessionId` ou `ProjectEncoded` errados, ou a sessão já foi apagada pela limpeza automática | confira o ID; para o futuro, ajuste `cleanupPeriodDays` |
| O `.bat` abre e avisa que o histórico não existe mais | passaram-se mais de 30 dias e o Claude Code apagou o transcript | não há como recuperar; o atalho pode ser apagado |
| Acentos embaralhados dentro do `.bat` | o `cmd` usa codepage OEM | o script já remove a acentuação do **conteúdo**; o **nome do arquivo** pode ter acentos normalmente |
| A aba não fica colorida | o Windows Terminal não está instalado (caiu no fallback) ou nenhuma cor foi gravada | instale o Windows Terminal; regrave mencionando a cor |
| Dois `.bat` da mesma conversa | os arquivos foram renomeados na mão, quebrando a busca pelo `SESSION_ID` | apague o duplicado e rode `/sessao-retorno` de novo |
| O atalho abre a conversa errada | o ID veio do `.jsonl` mais recente com várias janelas abertas no mesmo diretório | a skill deve usar o caminho do scratchpad como fonte primária |

## Estrutura

```
SKILL.md                     instruções para o agente
README.md                    este guia
scripts/gravar-sessao.ps1    escreve o .bat (validação, nome, cor, modo, idempotência)
```

## Como contribuir

Sugestões e melhorias são bem-vindas — principalmente de quem usa o Claude Code em várias janelas
ao mesmo tempo e conhece outros terminais.

1. **Faça um fork** e crie uma branch descritiva:
   ```bash
   git checkout -b melhoria/suporte-ao-alacritty
   ```
2. **Teste a alteração** gerando um atalho de verdade e conferindo o arquivo:
   ```powershell
   & .\scripts\gravar-sessao.ps1 -SessionId <id-real> -ProjectDir "<cwd>" `
       -ProjectEncoded "<pasta-em-.claude\projects>" -Assunto "teste"
   Get-Content "$env:USERPROFILE\Desktop\Sessoes Claude\*teste.bat"
   ```
   Confira os quatro comportamentos que sustentam a skill: aborta com sessão inexistente; não
   duplica atalho da mesma sessão; herda a cor ao regravar sem `-Cor`; detecta o modo do
   transcript.
3. **Abra o Pull Request** descrevendo o problema que a mudança resolve e o que muda no `.bat`
   gerado (cole o antes e o depois).

**O que não enviar no PR:**

- `.bat` gerados, IDs de sessão reais ou trechos de transcript — eles contêm o conteúdo das suas
  conversas;
- caminhos da sua máquina (`C:\Users\<seu-usuario>\...`), nomes de clientes, hosts ou usuários —
  os exemplos do repositório usam valores fictícios de propósito, mantenha assim.

Dúvida sobre o desenho antes de investir tempo? Abra uma issue — outro terminal, outro sistema
operacional, outro formato de atalho — que a gente conversa antes do código.

## Licença

MIT — veja o `LICENSE` na raiz do repositório.
