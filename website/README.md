# School Day Grid marketing site

This directory contains the static marketing site for `schooldaygrid.com`.

## Cloudflare Pages

- Framework preset: `None`
- Build command: leave blank
- Build output directory: `website`
- Root directory: repository root

The `_headers` and `_redirects` files are applied automatically by Cloudflare Pages.

## Local preview

From the repository root:

```bash
python -m http.server 4173 --directory website
```
