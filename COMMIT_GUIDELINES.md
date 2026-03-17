# COMMIT GUIDELINES

## Branch naming 

| Branch name <type>/<scope>/<short_description> | Description                                   | Example branch naming |
|:-----------------------------------------------|:----------------------------------------------|:----------------------|
| feat/<scope>                                   | New feature                                   | feat/chat             | 
| fix/<scope>                                    | Bug fix                                       | fix/bot               |
| docs/<scope>                                   | Docs changes                                  | docs/readme           |
| style/<scope>                                  | Formatting, spacing, no impact                | style/code            |
| refactor/<scope>>                              | Code restructuring without feature, no impact | refactor/api          |
| test/<scope>                                   | Add/change tests                              | test/bot              |
| chore/<scope>                                  | Maintenance / Administrative tasks            | chore/ci              | 

## Branch naming - details

- the <type> is the first option from the branch naming ()
- the <scope> in the branch naming represents the affected zone (e.g. 'chat', 'api', 'ui')


## Commit rules

| Commit structure type(scope): <short_description> | Description                                   | Example commit message                                        |
|:--------------------------------------------------|:----------------------------------------------|:--------------------------------------------------------------|
| feat(scope): <short_description>                  | New feature                                   | feat(chat): add a parser for emoji shortcuts in user messages | 
| fix(scope): <short_description>                   | Bug fix                                       | fix(bot): prevent crash when input is empty                   |
| docs(scope): <short_description>                  | Docs changes                                  | docs(readme): clarify installation steps                      |
| style(scope): <short_description>                 | Formatting, spacing, no impact                | style(code): reformat code for consistent spacing             |
| refactor(scope): <short_description>              | Code restructuring without feature, no impact | refacto(api): remove redundant code and improve readability   |
| test(scope): <short_description>                  | Add/change tests                              | test(bot): cover edge cases for message parsing               |
| chore(scope): <short_description>                 | Maintenance / Administrative tasks            | chore(ci): upgrade Flask version in CI                        | 


## Rules and good practice

- The message must be concise and clear
- Use imperative mood ('add', 'fix', 'update')
- Do NOT include specific bug-related details in separate branches
- Do NOT use obscure abbreviations (e.g. "fixes/bot/#12 OK", "f/api/#12 no")

## Refrences / Workflow

- link to CONTRIBUTING.md
- link to commit validation tool