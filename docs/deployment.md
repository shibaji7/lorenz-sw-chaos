# Deployment

This documentation site is configured to publish with GitHub Pages.

## Current setup

- source docs live in `docs/`
- MkDocs builds the static site into `site/`
- the GitHub Actions workflow in `.github/workflows/docs.yml` builds the docs
  on pushes to `main`
- the workflow publishes the generated `site/` directory to GitHub Pages
- if `docs/CNAME` exists, the workflow copies it into the published site root so
  a custom domain can be used without changing the workflow

## What you need in GitHub

To make the site public, enable GitHub Pages for the repository and select
"GitHub Actions" as the publishing source.

Once that is active, every push to `main` will rebuild and republish the docs.

## Optional custom domain

If you want a custom domain, create `docs/CNAME` containing only the domain
name, for example:

```text
docs.yourdomain.org
```

The workflow will copy that file into the published site root.

## Why GitHub Pages was chosen here

GitHub Pages is the simplest option for this repository because:

- the docs are already static
- the repository already uses GitHub Actions
- the output is a simple MkDocs site, so no extra server is needed

## Alternative

Read the Docs would also work if you want versioned docs with releases and a
`latest`/`stable` split. That is a good alternative if the documentation becomes
release-driven.

The repository also includes a `readthedocs.yml` file so the same MkDocs site
can be built there with minimal extra setup.
