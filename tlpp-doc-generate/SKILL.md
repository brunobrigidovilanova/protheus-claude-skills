---
name: tlpp-doc-generate
description: "Use SOMENTE quando o usuário pedir explicitamente para gerar documentação OpenAPI/Swagger de APIs REST TLPP — gatilhos: 'tlpp.doc.generate', 'REST-DOC', 'gerar documentação da API', 'YAML OpenAPI', 'swagger do Protheus', 'explorador openapi', 'documentar endpoints TLPP'. Se detectar que o usuário está criando um projeto TLPP com API REST sem ter pedido documentação, apenas SUGIRA esta skill em uma frase e aguarde confirmação explícita — nunca execute por conta própria."
license: MIT
metadata:
  domain: Protheus
  author: Bruno Brigido Vilanova
  version: '1.0.0'
  category: Documentation
---

# tlpp-doc-generate — Documentação OpenAPI de APIs REST TLPP

## Overview

Gera especificação **OpenAPI 3.x (YAML)** a partir das annotations do código REST TLPP, usando o motor **REST-DOC do tlppCore** (`tlpp.doc.generate()`), e prepara o resultado para o **Explorador OpenAPI** da TOTVS. Fluxo validado em ambiente Protheus 12.1.2510.

## Quando usar / não usar

- **Usar**: somente a pedido explícito do usuário (ver description).
- **Sugerir (sem executar)**: ao notar projeto TLPP com endpoints `@Get/@Post` sendo criado, ofereça em UMA frase ("quer que eu gere a documentação OpenAPI com a skill tlpp-doc-generate?") e pare.
- **Não usar**: APIs WSRESTFUL legadas (annotations REST-DOC não se aplicam); documentação de código-fonte (use ProtheusDOC).

## Etapa 0 — OBRIGATÓRIA: confirmar requisitos com o usuário

Antes de qualquer código, **valide com o usuário** (pergunte o que não puder verificar sozinho):

| Requisito | Como verificar |
|-----------|----------------|
| tlppCore **>= 01.04.02** | Perguntar ao usuário ou testar chamando `tlpp.doc.generate` (erro = versão antiga) |
| AppServer **>= 20.3.1.10** | Banner do console/log do AppServer |
| REST server ativo | `appserver.ini`: seções `[HTTPV11]`/`[HTTPREST]` (porta) e `[HTTPURI]` (URL, ex. `/rest`) |
| Includes TLPP (`tlpp-core.th`, `tlpp-rest.th`) | Perguntar ao usuário o caminho da pasta de includes do ambiente |
| Ambiente **local ou TCloud**? | TCloud: sem acesso a INI/filesystem — config via chamado; YAML via endpoint de download (ver README) |
| `SECURITY=1`? | Se sim, chamadas REST exigem Basic auth — pedir usuário/senha Protheus ao usuário (nunca gravar em arquivo versionado) |
| Porta(s) e idioma(s) a documentar | Confirmar com o usuário (ex.: `{8080}`, `{"pt-br"}`) |

Só prossiga depois que o usuário confirmar os itens que dependem dele.

## Fluxo

1. **Anotar os endpoints** com metadados nas annotations. Em fonte custom sem chave de compilação, **use `User Function`** (o compilador rejeita `function` plana):

```advpl
#include "tlpp-core.th"
#include "tlpp-rest.th"

@Get(;
    endpoint="/demo/v1/produtos",;
    title="Lista produtos",;
    description="Retorna a coleção no padrão TTALK.",;
    params='[{"name":"categoria","description":"Filtro","in":"query","type":"character","required":false}]',;
    responses='[{"statusCode":200,"description":"OK"}]';
)
user function zProdList() as logical
    // ...
return oRest:setStatusResponse(200, jResp:toJson())
```

`title` → `summary`; `:id` no endpoint → `{id}`; `params` aceita `in`: query/path/body.

2. **Criar endpoint gerador** que chama:

```advpl
tlpp.doc.generate("swagger", "api_doc", {<porta>}, {"pt-br"})
```

(1º param sempre `"swagger"`; saída `api_doc_<porta>.yaml` em `protheus_data\system\`.)

3. **Converter fonte para CP1252** e **compilar** — via TDS, ou por linha de comando com serviços parados:

```powershell
& "<bin>\appserver.exe" -compile -files="<fonte.tlpp>" -includes="<pasta-includes-tlpp>" -env=<ambiente>
```

4. **Subir serviços** (License → DBAccess → AppServer) e **chamar o gerador**: `curl -u usuario:senha "http://<host>:<porta>/rest/<endpoint-gerador>"`.

5. **Pós-processar o YAML** (ele sai em CP1252 e pode ter chaves de path duplicadas → `duplicated mapping key` no explorador):

```bash
python ~/.claude/skills/tlpp-doc-generate/scripts/fix_openapi_yaml.py <yaml-original> <yaml-corrigido>
```

6. **Explorador OpenAPI** — https://totvs.github.io/totvstec-doc/tools/explorador-openapi — colar/upload do YAML corrigido. Para "Try it": Base URL = `http://<host>:<porta-rest>/rest` (NÃO a porta do WebApp); header `Authorization: Basic <base64 usuario:senha>`; CORS no `appserver.ini` (seção `[HTTPURI]`): `CORSEnable=1` + `AllowOrigin=*` (dev) e reiniciar o AppServer.

## Erros comuns

| Sintoma | Causa | Correção |
|---------|-------|----------|
| "Regular functions are not allowed" | `function` plana em fonte custom | `User Function`/`Static Function` |
| `duplicated mapping key` no explorador | Motor emite um bloco por verbo em paths repetidos | `scripts/fix_openapi_yaml.py` |
| Acentos corrompidos no YAML | Arquivo gerado em CP1252 | `scripts/fix_openapi_yaml.py` (grava UTF-8) |
| 404 no Try it | Base URL na porta do WebApp | Usar porta REST + `/rest` |
| 401 no Try it | `SECURITY=1` | Header `Authorization: Basic ...` manual |
| Bloqueio CORS no navegador | Sem CORS no REST | `CORSEnable=1`/`AllowOrigin` em `[HTTPURI]` + restart |

## Links

- TDN Gerador de documentação: https://tdn.totvs.com/pages/viewpage.action?pageId=745121740
- Exemplos oficiais: https://github.com/totvs/tlpp-sample-rest-documentation
- Metadados REST: https://totvs.github.io/totvstec-doc/docs/tlpp/rest/metadados/visao-geral
- Exemplo completo: `examples/zRestDocDemo.tlpp` (nesta pasta)
