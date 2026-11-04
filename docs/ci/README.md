# Optional CI workflow

[`ci-example.yml`](ci-example.yml) is a ready-to-use GitHub Actions workflow that rebuilds `frontend/index.html` from `src/`, verifies the 137-paper dataset, checks Python syntax and uploads the built page as an artefact.

## Enable it

```bash
mkdir -p .github/workflows
cp docs/ci/ci-example.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml && git commit -m "ci: validate frontend build"
git push
```

> **Note:** GitHub blocks creating or updating `.github/workflows/*.yml` with an OAuth App token that lacks the `workflow` scope. If you see
> `refusing to allow an OAuth App to create or update workflow ... without workflow scope`,
> push that one commit with a Personal Access Token that includes `workflow`, or with the GitHub CLI after `gh auth refresh -s workflow`.

The repository works perfectly without CI — it is pure documentation/automation polish for a school project.
