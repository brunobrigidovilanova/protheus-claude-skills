# protheus-claude-skills

Skills do [Claude Code](https://claude.com/claude-code) para desenvolvimento **TOTVS Protheus (AdvPL/TLPP)**.

Cada skill é uma pasta com um `SKILL.md` (instruções que o Claude carrega) e um `README.md` com o **guia completo** — clique no link da tabela abaixo para abrir a pasta da skill e ler o guia renderizado.

## Instalação

Copie a pasta da skill desejada para o diretório global de skills do Claude Code:

```powershell
# Windows
Copy-Item -Recurse .\tlpp-doc-generate "$env:USERPROFILE\.claude\skills\"
```

```bash
# Linux / macOS
cp -r ./tlpp-doc-generate ~/.claude/skills/
```

Na próxima sessão (ou na atual, em alguns clientes), a skill aparece automaticamente na lista de skills disponíveis.

## Skills

| Skill | Categoria | Descrição | Guia |
|-------|-----------|-----------|------|
| [tlpp-doc-generate](tlpp-doc-generate/) | Documentação | Gera documentação **OpenAPI 3.x (YAML)** de APIs REST TLPP com `tlpp.doc.generate()` (motor REST-DOC do tlppCore) e prepara o resultado para o [Explorador OpenAPI da TOTVS](https://totvs.github.io/totvstec-doc/tools/explorador-openapi). Inclui script de correção do YAML (encoding + chaves duplicadas). | 📖 [Guia completo](tlpp-doc-generate/) |

> Mais skills serão adicionadas aqui. Sugestões e contribuições são bem-vindas via issue ou PR.

## Adicionando uma nova skill

1. Crie uma pasta na raiz com o nome da skill em kebab-case (ex.: `minha-skill/`).
2. Dentro dela, crie:
   - `SKILL.md` — frontmatter YAML com `name` e `description` (a description define **quando** o Claude deve ativar a skill) + as instruções;
   - `README.md` — guia completo para humanos (requisitos, passo a passo, armadilhas);
   - `scripts/`, `examples/`, `references/` — opcionais, para ferramentas e materiais de apoio.
3. Adicione uma linha na tabela acima com o resumo e o link `📖 [Guia completo](minha-skill/)`.

## Convenções

- Fontes AdvPL/TLPP de exemplo ficam em **UTF-8** no repositório (padrão git/GitHub). O compilador Protheus exige **Windows-1252 (CP1252)** — converta antes de compilar (os guias indicam como).
- Nenhum arquivo do repositório contém credenciais ou dados reais de ambiente — os guias usam **valores de exemplo**; substitua pelos do seu ambiente.

## Licença

[MIT](LICENSE)
