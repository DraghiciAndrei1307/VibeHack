# COMMIT GUIDELINES

## 📌 Mandatory branches

- `vibehack`: this branch will remain unchanged as a reminder of the achievements of the VibeHack hackathon
- `prod`/`main`: used in production environments
- `dev`: used in non-productive environments
- `test`: 
  - used to test databases for testing purposes
  - this branch is not for unfinished changes (
  - test unfinished work on your own test environment
  - put changes you consider finished on this branch for final tests

## 🏷️ Branch naming 

| Branch name type/scope | Description                                   | Example branch naming |
|:-----------------------|:----------------------------------------------|:----------------------|
| feat/scope             | New feature                                   | feat/chat             | 
| fix/scope              | Bug fix                                       | fix/bot               |
| docs/scope             | Docs changes                                  | docs/readme           |
| style/scope            | Formatting, spacing, no impact                | style/code            |
| refactor/scope         | Code restructuring without feature, no impact | refactor/api          |
| test/scope             | Add/change tests                              | test/bot              |
| chore/scope            | Maintenance / Administrative tasks            | chore/ci              | 

## 🔍 Branch naming - details

- the <type> is the first option from the branch naming ()
- the <scope> in the branch naming represents the affected zone (e.g. 'chat', 'api', 'ui')


## ⚖️ Commit rules

| Commit structure type(scope): <short_description> | Description                                   | Example commit message                                        |
|:--------------------------------------------------|:----------------------------------------------|:--------------------------------------------------------------|
| feat(scope): <short_description>                  | New feature                                   | feat(chat): add a parser for emoji shortcuts in user messages | 
| fix(scope): <short_description>                   | Bug fix                                       | fix(bot): prevent crash when input is empty                   |
| docs(scope): <short_description>                  | Docs changes                                  | docs(readme): clarify installation steps                      |
| style(scope): <short_description>                 | Formatting, spacing, no impact                | style(code): reformat code for consistent spacing             |
| refactor(scope): <short_description>              | Code restructuring without feature, no impact | refacto(api): remove redundant code and improve readability   |
| test(scope): <short_description>                  | Add/change tests                              | test(bot): cover edge cases for message parsing               |
| chore(scope): <short_description>                 | Maintenance / Administrative tasks            | chore(ci): upgrade Flask version in CI                        | 


## ✔️ Rules and good practice

- The message must be concise and clear
- Use imperative mood ('add', 'fix', 'update')
- Do NOT include specific bug-related details in separate branches
- Do NOT use obscure abbreviations (e.g. "fixes/bot/#12 OK", "f/api/#12 no")

## 🧭 How to work with branches

1) Create a new branch
   - Always do this from productive
   - Obey the naming convention described above

2) Create changes and commits
   - Make sure the commits have names that can let people understand their purpose
3) Merge from productive into your branch
   - This is not necessary but ensures you have the newest changes from prod on your branch
4) Create a Pull request to merge your changes into 'test'
   - If there are problems with the changes, repeat steps 2,3,4
5) Create Pull request to merge your changes into 'dev'
6) Create pull request to merge your changes into 'prod'
7) YOU MUST NOT MAKE ANY CHANGES ON YOUR BRANCH BETWEEN MERGING TO test, dev and prod !!!!
   - Use merge, NOT rebase !!!
8) Delete your branch or move it to the archive space
   - to delete a branch on the remote use a tool such as 'GitHub Desktop' or 'Sourcetree' or run 
   `git push origin -d type/scope`
   - to move it into the archive space you need to rename the branch
     - you can use a tool for this
     - or you can create a new branch from yours with the same name except for the space being 'archive', publish it
     on the remote and delete the old one 

## 🔗 Refrences / Workflow

- [PULL_REQUEST_GUIDELINES.md](PULL_REQUEST_GUIDELINES.md)
- [work_with_branches.mmd](work_with_branches.mmd)