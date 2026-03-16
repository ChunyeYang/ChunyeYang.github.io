# ChunyeYang.github.io

Static GitHub Pages site for Chunye Yang.

## Content workflow

1. Edit `site.yaml`
2. Run `python3 generate_site.py`
3. Commit and push `index.html`, `topics/*.html`, and any new PDFs

## YAML shape

```yaml
name: Chunye Yang
email: chunye@umich.edu

sections:
  Reading Notes:
    Topic Name:
      - title: File title
        path: some-file.pdf

    Topic With Extras:
      external_url: https://arxiv.org/abs/xxxx.xxxxx
      files:
        - title: First PDF
          path: first.pdf
        - title: Second PDF
          path: second.pdf
```

Rules:
- top-level `sections` controls homepage section order
- each section maps topic names to topic entries
- if a topic has one PDF, the homepage topic link goes directly to that PDF
- if a topic has multiple PDFs, the homepage topic link goes to a generated topic page
- `external_url` is optional and can be used for arXiv or other external references
