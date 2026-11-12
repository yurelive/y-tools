# y-tools

Repositório de ferramentas pessoais em Python. Cada tool é um subpacote de
`src/y_tools/` e tem um notebook em `notebooks/` para explorar e testar.

## Convenções

- Código, docstrings, comentários e commits em português.
- Docstrings estilo Google (`Args:`, `Returns:`, `Raises:`) e type hints em tudo.
- Constantes de módulo documentadas com docstring logo abaixo.
- Caminhos sempre via `y_tools.paths` (absolutos a partir da raiz do repo), nunca
  relativos ao diretório de trabalho — notebooks e CLI rodam de pastas diferentes.
- Logs via `y_tools.logger.setup_logger`, nunca `print` dentro de `src/`.
- Notebooks importam o pacote instalado (`pip install -e .`), sem `sys.path.insert`.
- Notebooks são commitados sem saídas (filtro `nbstripout` no `.gitattributes`).
- `data/`, `output/` e `logs/` ficam fora do git — podem ter conteúdo pessoal.
- Testes não baixam modelos nem acessam rede: use `monkeypatch`/fakes.
- Commits no padrão Conventional Commits, modo imperativo.

## Estilo de Comentários com Better Comments

Para manter a legibilidade e padronização dos comentários no código, utilize a extensão **Better Comments** do VS Code.

### utilizando a extensão

Para utilizar a extensão, adicione no início do seu comentário o símbolo correspondente da tabela abaixo, seguido do texto desejado.
Exemplo de uso no código:

| Tag    | Descrição                      | Exemplo                              |
| ------ | ------------------------------ | ------------------------------------ |
| `#`    | Títulos ou seções no código    | `# Seção: Inicialização`             |
| `*`    | Informações importantes        | `* Validação obrigatória`            |
| `!`    | Alertas ou erros críticos      | `! Corrigir lógica de autenticação`  |
| `?`    | Perguntas ou pontos de atenção | `? Melhor usar async/await aqui?`    |
| `//`   | Código comentado ou obsoleto   | `// função antiga()`                 |
| `TODO` | Tarefas pendentes              | `//TODO: Adicionar testes unitários` |
