# 🤝 Guia de Contribuição

## Fluxo de Trabalho

```bash
git checkout main
git pull
git checkout -b feature/nome-da-feature
```

Exemplos:

- feature/transcricao-diarizacao
- fix/transcricao-timestamps-srt
- refactor/paths

## Padrão de Commits

[Conventional Commits](https://www.conventionalcommits.org/pt-br/), no modo imperativo
(regras em `.commitlintrc.json`):

```text
feat(transcricao): adiciona exportação em VTT
fix(transcricao): corrige arredondamento dos milissegundos no SRT
docs: atualiza readme
refactor: reorganiza paths
```

## Boas Práticas

- Utilizar type hints e docstrings em português
- Criar funções pequenas e reutilizáveis em `src/`; notebooks só orquestram
- Tratar exceções adequadamente
- Não armazenar credenciais no código — use `.env` (ver `.env.example`)
- Registrar logs relevantes com `y_tools.logger`

## Antes de abrir o PR

```bash
black src tests
isort src tests
flake8 src tests
pytest
```

## Code Review

Antes do merge:

- [ ] Código testado
- [ ] Sem credenciais hardcoded
- [ ] Notebooks sem saídas (o `nbstripout` cuida disso)
- [ ] Logs validados
- [ ] Documentação atualizada
- [ ] Dependências documentadas

## Segurança

- Nunca commitar `.env`
- Nunca commitar tokens ou senhas
- Nunca commitar áudios, transcrições ou outros dados pessoais (`data/`, `output/`)

Segurança sempre vem primeiro.
