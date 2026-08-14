<#
.SYNOPSIS
    Gera um atalho .bat que reabre uma sessao do Claude Code (claude --resume).

.DESCRIPTION
    Chamado pela skill /sessao-retorno. Valida que o transcript da sessao existe,
    monta um nome de arquivo a partir da data + assunto, e grava um .bat que
    abre o Windows Terminal (com fallback para powershell.exe) no diretorio
    do projeto ja retomando aquela sessao.

    Idempotente: se ja existir um .bat para o mesmo SessionId na pasta, ele e
    atualizado (e renomeado, se o assunto mudou) em vez de duplicado.

.EXAMPLE
    .\gravar-sessao.ps1 -SessionId 00000000-1111-2222-3333-444444444444 `
                        -ProjectDir "C:\Projetos\MinhaApp" `
                        -ProjectEncoded "C--Projetos-MinhaApp" `
                        -Assunto "Refatoracao do modulo de pedidos" `
                        -Cor azul
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $SessionId,
    [Parameter(Mandatory = $true)] [string] $ProjectDir,
    [Parameter(Mandatory = $true)] [string] $ProjectEncoded,
    [Parameter(Mandatory = $true)] [string] $Assunto,
    [string] $Cor = '',
    [string] $Modo = '',
    [string] $Pasta = "$env:USERPROFILE\Desktop\Sessoes Claude"
)

$ErrorActionPreference = 'Stop'

# Cores aceitas em -Cor (nome em pt-BR ou hex #RRGGBB). Paleta Campbell do
# Windows Terminal, para a aba combinar com o tema padrao.
$CORES = @{
    'vermelho' = '#C50F1F'
    'verde'    = '#13A10E'
    'azul'     = '#0037DA'
    'ciano'    = '#3A96DD'
    'amarelo'  = '#C19C00'
    'roxo'     = '#881798'
    'laranja'  = '#FF8C00'
    'rosa'     = '#E74856'
    'cinza'    = '#767676'
}

# Modos de permissao aceitos por `claude --permission-mode` (v2.1.229).
# 'default' nao aparece na lista de choices do --help, mas e aceito.
$MODOS = @('acceptEdits', 'auto', 'bypassPermissions', 'manual', 'dontAsk', 'plan', 'default')

# Le o ultimo "permissionMode" gravado no transcript = o modo em que a sessao
# estava. Le so o fim do arquivo: transcripts passam de 10 MB com facilidade.
function Get-ModoDaSessao([string]$arquivo) {
    $rx = [regex]'"permissionMode"\s*:\s*"(\w+)"'
    $fs = [System.IO.File]::OpenRead($arquivo)
    try {
        $tam = [int][Math]::Min(524288, $fs.Length)
        $fs.Seek(-$tam, [System.IO.SeekOrigin]::End) | Out-Null
        $buf = New-Object byte[] $tam
        $fs.Read($buf, 0, $tam) | Out-Null
    } finally { $fs.Dispose() }
    $ms = $rx.Matches([System.Text.Encoding]::UTF8.GetString($buf))
    if ($ms.Count) { return $ms[$ms.Count - 1].Groups[1].Value }
    return ''
}

# --- 1. Valida o transcript da sessao ------------------------------------
$transcript = Join-Path $env:USERPROFILE ".claude\projects\$ProjectEncoded\$SessionId.jsonl"
if (-not (Test-Path -LiteralPath $transcript)) {
    Write-Error @"
Transcript nao encontrado: $transcript
O SessionId ou o ProjectEncoded estao errados, ou a sessao ja foi removida
pela limpeza automatica do Claude Code. Nenhum atalho foi gerado.
"@
    exit 1
}

# --- 2. Garante a pasta de destino ---------------------------------------
if (-not (Test-Path -LiteralPath $Pasta)) {
    New-Item -ItemType Directory -Path $Pasta -Force | Out-Null
}

# --- 3. Monta o nome do arquivo ------------------------------------------
$limpo = $Assunto -replace '[\\/:*?"<>|]', ' '
$limpo = ($limpo -replace '\s+', ' ').Trim(' ', '.', '-')
if ([string]::IsNullOrWhiteSpace($limpo)) { $limpo = 'Sessao Claude' }
if ($limpo.Length -gt 70) { $limpo = $limpo.Substring(0, 70).Trim() }

$hoje       = Get-Date -Format 'yyyy-MM-dd'
$agora      = Get-Date -Format 'yyyy-MM-dd HH:mm'
$nomeArq    = "$hoje - $limpo.bat"
$destino    = Join-Path $Pasta $nomeArq

# --- 4. Idempotencia: ja existe atalho para esta sessao? -----------------
$existente = Get-ChildItem -LiteralPath $Pasta -Filter '*.bat' -File -ErrorAction SilentlyContinue |
    Where-Object { Select-String -LiteralPath $_.FullName -Pattern ([regex]::Escape($SessionId)) -Quiet }

$acao = 'criado'
$corHerdada = ''
if ($existente) {
    $antigo = $existente | Select-Object -First 1
    # Se o atalho ja tinha cor de aba e nenhuma foi informada agora, preserva.
    $m = Select-String -LiteralPath $antigo.FullName -Pattern '--tabColor "(#[0-9A-Fa-f]{6})"' |
         Select-Object -First 1
    if ($m) { $corHerdada = $m.Matches[0].Groups[1].Value }

    if ($antigo.FullName -ne $destino) {
        Remove-Item -LiteralPath $antigo.FullName -Force
        $acao = 'renomeado'
    } else {
        $acao = 'atualizado'
    }
    # Atalhos extras para a mesma sessao (se houver) sao removidos.
    $existente | Where-Object { $_.FullName -ne $antigo.FullName } | Remove-Item -Force
}

# --- 4b. Resolve a cor da aba --------------------------------------------
$corHex = ''
if (-not [string]::IsNullOrWhiteSpace($Cor)) {
    $chave = $Cor.Trim().ToLower()
    if ($CORES.ContainsKey($chave)) {
        $corHex = $CORES[$chave]
    } elseif ($chave -match '^#?[0-9a-f]{6}$') {
        $corHex = '#' + $chave.TrimStart('#').ToUpper()
    } else {
        Write-Error "Cor invalida: '$Cor'. Use um hex #RRGGBB ou um destes nomes: $(($CORES.Keys | Sort-Object) -join ', ')."
        exit 1
    }
} else {
    $corHex = $corHerdada   # mantem a cor que o atalho ja tinha
}

$tabColorArg = ''
$corLinha    = '(padrao do Windows Terminal)'
if ($corHex) {
    $tabColorArg = " --tabColor `"$corHex`""
    $corLinha    = $corHex
}

# --- 4c. Resolve o modo de permissao -------------------------------------
$modoOrigem = 'informado'
if ([string]::IsNullOrWhiteSpace($Modo)) {
    $Modo = Get-ModoDaSessao $transcript
    $modoOrigem = 'detectado no transcript'
}

$modoArg   = ''
$modoLinha = '(o que o Claude Code usar por padrao)'
if ($Modo) {
    if ($MODOS -notcontains $Modo) {
        if ($modoOrigem -eq 'informado') {
            Write-Error "Modo invalido: '$Modo'. Use um destes: $($MODOS -join ', ')."
            exit 1
        }
        # Modo desconhecido vindo do transcript (versao nova do CLI?): ignora em
        # vez de gerar um .bat que o claude recusa a abrir.
        Write-Warning "Modo '$Modo' nao reconhecido no transcript - o atalho vai abrir sem --permission-mode."
        $Modo = ''
    } else {
        $modoArg   = " --permission-mode $Modo"
        $modoLinha = "$Modo ($modoOrigem)"
    }
}

# --- 5. Conteudo do .bat (ASCII, sem acentos) ----------------------------
$assuntoBat = ($Assunto -replace '[\r\n]', ' ')
$assuntoBat = ($assuntoBat -replace '[<>|&^%]', ' ').Trim()

$conteudo = @"
@echo off
REM ============================================================
REM  Sessao Claude Code - gravada por /sessao-retorno
REM  Data....: $agora
REM  Projeto.: $ProjectDir
REM  Assunto.: $assuntoBat
REM  Cor aba.: $corLinha
REM  Modo....: $modoLinha
REM  Session.: $SessionId
REM ============================================================
setlocal
set "SESSAO=$SessionId"
set "PROJETO=$ProjectDir"
set "TRANSCRIPT=%USERPROFILE%\.claude\projects\$ProjectEncoded\%SESSAO%.jsonl"

if not exist "%TRANSCRIPT%" (
  echo.
  echo [ERRO] O historico desta sessao nao existe mais:
  echo        %TRANSCRIPT%
  echo        Provavelmente foi removido pela limpeza automatica do Claude Code.
  echo.
  pause
  exit /b 1
)

set "CLAUDE=%USERPROFILE%\.local\bin\claude.exe"
if not exist "%CLAUDE%" set "CLAUDE=claude"

echo Retomando: $assuntoBat

where wt.exe >nul 2>&1
if %errorlevel%==0 (
  start "" wt.exe -d "%PROJETO%"$tabColorArg powershell.exe -NoExit -NoProfile -Command "& '%CLAUDE%' --resume %SESSAO%$modoArg %*"
) else (
  start "" powershell.exe -NoExit -NoProfile -Command "Set-Location '%PROJETO%'; & '%CLAUDE%' --resume %SESSAO%$modoArg %*"
)
endlocal
"@

# Remove acentuacao do corpo do .bat (o cmd usa codepage OEM e embaralharia).
$semAcento = $conteudo.Normalize([Text.NormalizationForm]::FormD) -replace '\p{Mn}', ''

Set-Content -LiteralPath $destino -Value $semAcento -Encoding ASCII

# --- 6. Resultado --------------------------------------------------------
Write-Output "OK|$acao|$destino"
