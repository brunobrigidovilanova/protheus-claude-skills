# tlpp-doc-generate — Documentação OpenAPI de APIs REST TLPP

> Skill do Claude Code que gera especificação **OpenAPI 3.x (YAML)** a partir das annotations do código REST TLPP, usando o motor **REST-DOC do tlppCore** (`tlpp.doc.generate()`), e prepara o resultado para o [Explorador OpenAPI da TOTVS](https://totvs.github.io/totvstec-doc/tools/explorador-openapi).
>
> ⚠️ Todos os valores deste guia (paths, portas, URLs, usuários e senhas) são **exemplos** — substitua pelos do seu ambiente.

## O que é

O **REST-DOC** é o motor de documentação do **tlppCore** que lê os metadados (annotations) do código REST TLPP compilado no RPO e gera uma especificação **OpenAPI 3.x** em YAML — documentação viva, que nasce do próprio fonte. A função que dispara a geração é a **`tlpp.doc.generate()`**.

O YAML pode ser aberto no **Explorador OpenAPI** (ferramenta web da TOTVS, roda 100% no navegador): permite navegar pelos endpoints, ver parâmetros/respostas e **executar requisições reais** contra o AppServer.

## Requisitos

| Requisito | Detalhe |
|-----------|---------|
| tlppCore | **>= 01.04.02** |
| AppServer | **>= 20.3.1.10** (o banner do console/log mostra a versão) |
| REST configurado | Seções `[HTTPV11]` / `[HTTPREST]` / `[HTTPURI]` / `[HTTPJOB]` do `appserver.ini` |
| Includes TLPP | `tlpp-core.th`, `tlpp-rest.th` (pasta de includes do seu ambiente) |
| Encoding dos fontes | **CP1252** (o compilador Protheus não aceita UTF-8) |
| Autenticação | Com `SECURITY=1` no REST, toda chamada exige **Basic auth** (usuário Protheus) |

## Como implementar

Documente cada endpoint direto na annotation com `title`, `description`, `params` e `responses` (as duas últimas em JSON string). Em fonte **custom sem chave de compilação, use `User Function`** — o compilador rejeita `function` plana.

```advpl
#include "tlpp-core.th"
#include "tlpp-rest.th"

@Get(;
    endpoint="/demo/v1/produtos",;
    title="Lista produtos",;
    description="Retorna a coleção de produtos no padrão TTALK, com filtro opcional por categoria.",;
    params='[{"name":"categoria","description":"Filtra pela categoria","in":"query","type":"character","required":false}]',;
    responses='[{"statusCode":200,"description":"Coleção de produtos (items, hasNext, remainingRecords)"}]';
)
user function zProdList() as logical
    // ... monta a resposta ...
return oRest:setStatusResponse(200, jResp:toJson())
```

E um endpoint que dispara a geração do YAML:

```advpl
@Get(endpoint="/demo/v1/doc/generate", title="Gera documentação OpenAPI")
user function zDocGen() as logical
    begin sequence
        tlpp.doc.generate("swagger", "api_doc", {8080}, {"pt-br"})
    recover
        return oRest:setStatusResponse(500, '{"success":false}')
    end sequence
return oRest:setStatusResponse(200, '{"success":true}')
```

**Fonte completo de exemplo:** [`examples/zRestDocDemo.tlpp`](examples/zRestDocDemo.tlpp) (4 endpoints: GET coleção, GET por id com path param, POST com body e o gerador — dados estáticos, sem acesso a banco).

O que vira o quê no YAML: `title` → `summary` · `:id` no endpoint → `{id}` · `"type":"character"` → `type: string`.

### Parâmetros de `tlpp.doc.generate()`

| # | Parâmetro | Exemplo | Descrição |
|---|-----------|---------|-----------|
| 1 | Formato | `"swagger"` | Sempre `"swagger"` (gera OpenAPI 3.x; nome mantido por compatibilidade) |
| 2 | Nome base | `"api_doc"` | Nome do arquivo de saída |
| 3 | Portas | `{8080}` | Array com a(s) porta(s) REST cujos endpoints serão documentados |
| 4 | Idiomas | `{"pt-br"}` | Array de locales (para textos via i18n) |
| 5 | Função de lista *(opcional)* | `"U_ListDOCFunctions"` | Mapeamento dinâmico de rotas → funções `_DOC` |

**Saída:** `<nome>_<porta>.yaml` (ex.: `api_doc_8080.yaml`) gravado em **`protheus_data\system\`** do ambiente.

## Como executar — base LOCAL

Valores de exemplo: Protheus em `C:\TOTVS\Protheus`, ambiente `ENVIRONMENT`, REST na porta `8080`, usuário `usuario.rest` / senha `SuaSenha@123`.

1. **Converter o fonte para CP1252** (arquivos criados por IA/editores modernos nascem UTF-8).
2. **Compilar** — via TDS (VS Code/Eclipse) ou por linha de comando com os serviços parados:

```powershell
& "C:\TOTVS\Protheus\bin\appserver\appserver.exe" -compile `
  -files="C:\projetos\minha-api\zRestDocDemo.tlpp" `
  -includes="C:\TOTVS\includes" `
  -env=ENVIRONMENT
```

3. **Subir os serviços** na ordem License Server → DBAccess → AppServer.
4. **Chamar o endpoint gerador** (com Basic auth, pois `SECURITY=1`):

```bash
curl -u usuario.rest:SuaSenha@123 "http://localhost:8080/rest/demo/v1/doc/generate"
```

5. **Pegar o YAML** em `C:\TOTVS\Protheus\protheus_data\system\api_doc_8080.yaml`.

## Como executar — base TCLOUD (TOTVS Cloud)

No TCloud você **não tem acesso direto** ao `appserver.ini` nem ao filesystem do servidor. URL de exemplo: `https://minhaempresa.protheus.cloudtotvs.com.br:4050/rest`.

| Etapa | Como fica no TCloud |
|-------|---------------------|
| Configurar REST / CORS / porta | **Chamado no Portal TOTVS Cloud** solicitando a configuração (`[HTTPREST]`, `[HTTPURI]`, `CORSEnable`/`AllowOrigin`) |
| Compilar | Via **TDS** conectado ao ambiente (não há linha de comando) |
| Chamar o gerador | `curl -u usuario.rest:SuaSenha@123 "https://minhaempresa.protheus.cloudtotvs.com.br:4050/rest/demo/v1/doc/generate"` |
| Recuperar o YAML | **Sem acesso a `protheus_data\system`** — crie um endpoint REST que lê o arquivo e retorna o conteúdo (exemplo abaixo) |

Endpoint auxiliar para baixar o YAML em ambientes sem acesso ao filesystem:

```advpl
@Get(endpoint="/demo/v1/doc/download", title="Baixa o YAML OpenAPI gerado")
user function zDocGet() as logical
    local cFile := "\system\api_doc_8080.yaml" as character
    local cYaml := "" as character

    if ( File(cFile) )
        cYaml := MemoRead(cFile)
        oRest:setKeyHeaderResponse("Content-Type", "application/yaml")
        return oRest:setStatusResponse(200, cYaml)
    endif

return oRest:setStatusResponse(404, '{"code":"404","message":"YAML ainda nao gerado"}')
```

## Pós-processamento do YAML (obrigatório)

O YAML sai com dois defeitos conhecidos:

1. **Encoding CP1252** (acentos corrompidos ao colar em ferramentas que esperam UTF-8);
2. **Chaves de path duplicadas** — o motor emite um bloco por verbo para o mesmo path, e o parser do explorador rejeita com `duplicated mapping key`.

O script [`scripts/fix_openapi_yaml.py`](scripts/fix_openapi_yaml.py) corrige os dois (mescla os blocos sem perder verbos e grava em UTF-8):

```bash
python scripts/fix_openapi_yaml.py api_doc_8080.yaml api_doc_8080_fixed.yaml
```

## Visualizar e testar no Explorador OpenAPI

1. Abra https://totvs.github.io/totvstec-doc/tools/explorador-openapi
2. **Cole ou faça upload** do YAML corrigido.
3. No "Try it": **Base URL** = `http://localhost:8080/rest` (local) ou `https://minhaempresa.protheus.cloudtotvs.com.br:4050/rest` (TCloud). ⚠️ Não use a porta do **WebApp** — dá 404.
4. No editor de **Headers**, adicione `Authorization` = `Basic <base64 de usuario:senha>`. Para gerar o valor:

```powershell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("usuario.rest:SuaSenha@123"))
```

5. Para o navegador não bloquear as chamadas, o REST precisa de **CORS** habilitado — na seção `[HTTPURI]` do `appserver.ini` (base local) ou via chamado (TCloud):

```ini
[HTTPURI]
URL=/rest
PrepareIn=All
Instances=1,2
CORSEnable=1
AllowOrigin=*
```

> ⚠️ `AllowOrigin=*` apenas em desenvolvimento. Em produção, restrinja: `AllowOrigin=https://dominio1.com,https://dominio2.com`.

## Armadilhas conhecidas

| Sintoma | Causa | Correção |
|---------|-------|----------|
| `Regular functions are not allowed` na compilação | `function` plana em fonte custom sem chave de compilação | Usar `User Function` / `Static Function` |
| `duplicated mapping key` no explorador | Motor emite um bloco por verbo em paths repetidos | `scripts/fix_openapi_yaml.py` |
| Acentos corrompidos no YAML | Arquivo gerado em CP1252 | `scripts/fix_openapi_yaml.py` (grava UTF-8) |
| 404 Not Found no Try it | Base URL apontando para a porta do WebApp | Usar a porta REST + `/rest` |
| 401 Unauthorized | REST com `SECURITY=1` | Header `Authorization: Basic ...` manual nos headers |
| Erro de CORS no console do navegador | REST sem CORS | `CORSEnable=1`/`AllowOrigin` em `[HTTPURI]` + reiniciar AppServer |
| 503 "API não permitida" | `SECURITY=0` no REST | Habilitar `SECURITY=1` |

## Links

- **Explorador OpenAPI:** https://totvs.github.io/totvstec-doc/tools/explorador-openapi
- **TDN — Gerador de documentação (tlppCore):** https://tdn.totvs.com/pages/viewpage.action?pageId=745121740
- **Repositório de exemplos oficiais TOTVS:** https://github.com/totvs/tlpp-sample-rest-documentation
- **Documentação dos metadados REST:** https://totvs.github.io/totvstec-doc/docs/tlpp/rest/metadados/visao-geral
- **TDN — Exemplo CORS:** https://tdn.totvs.com/display/framework/Exemplo+CORS

## Conteúdo da pasta

| Arquivo | Descrição |
|---------|-----------|
| [`SKILL.md`](SKILL.md) | Instruções que o Claude Code carrega (ativação, requisitos, fluxo) |
| [`scripts/fix_openapi_yaml.py`](scripts/fix_openapi_yaml.py) | Corrige encoding e chaves duplicadas do YAML gerado |
| [`examples/zRestDocDemo.tlpp`](examples/zRestDocDemo.tlpp) | API de demonstração completa (em UTF-8 — converta para CP1252 antes de compilar) |
