# PULL REQUEST GUIDELINES

## 1. When to create a PR
- Create a PR for **every feature, bug fix, or refactor** branch.
- PRs should represent **a single, coherent change**.
- Target branch is usually `main` or `develop` depending on repo workflow.

## 2. Branch naming
- Follow **COMMIT_GUIDELINES.md** branch naming:
  - `feat/<scope>/<short-description>`
  - `fix/<scope>/<short-description>`
  - `refactor/<scope>/<short-description>`
  - `chore/<scope>/<short-description>`
- Keep it **short, descriptive, and consistent**.

## 3. PR title
- Format PR title similarly to commit messages:

```<type>(<scope>): <short description>```

**Example**

```
refactor(structure): reorganize folders and document workflow
```

## 4. PR description
- Include **what changed** and **why**.
- Include **related issues** (e.g., `Closes #12`, `Relates to #15`).
- Optional: describe **how to test** the changes.

**Example PR description:**

```
Description:

Reorganized project folders and moved documentation into proper directories.
```

## 5. Checklist before submitting
- [ ] Branch follows branch naming rules
- [ ] Commits follow COMMIT_GUIDELINES.md
- [ ] Code builds successfully and passes tests
- [ ] Documentation updated if necessary
- [ ] No sensitive information included

## 6. Review process
- PR will be reviewed by at least **one team member**
- Reviewer can request changes, approve, or comment
- After approval and passing CI/CD, PR can be merged
- Delete branch after merge to keep repo clean