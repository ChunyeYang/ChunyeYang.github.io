# ChunyeYang.github.io

Static GitHub Pages site for Chunye Yang.

## Content workflow

1. Edit `site.yaml`
2. Run `python3 generate_site.py deploy`

## YAML shape

```yaml
name: Chunye Yang
email: chunye@umich.edu
bio: |
  Write your self-description here.
  You can use multiple lines.

sections:
  Reading Notes:
    Etale Cohomology:
      description: Notes from a first reading seminar.
      files:
        - title: Etale Cohomology/Descent theory
          description: Descent data and fpqc descent.
        - title: Etale Cohomology/Etale and smooth morphisms
          description: Basic definitions and local structure.
        - title: Etale Cohomology/Etale covering spaces

    Intro to Homological Algebra: Intro to Homological Algebra/Intro to Homological Algebra

    Rising Sea Notes and Exercises:
      description: Short notes and exercises.
      file: FOAG Rising Sea/Blow-up

  Seminar Notes: {}

  Research & Publications:
    Representation stability in the (co)homology of vertical configuration spaces:
      link: https://arxiv.org/abs/xxxx.xxxxx
      description: Preprint on representation stability in vertical configuration spaces.
```

Edit the top-level `bio` field to update the “About me” text beneath your email on every page. Use `bio: |` with indented lines to preserve line breaks. Leave it blank until you are ready to add your description. Text is displayed as plain text, not HTML. Run `python3 generate_site.py deploy` to publish it.

Rules:
- top-level `sections` controls homepage navigation order; each section has a separate page under `sections/`
- `Seminar Notes: {}` creates an empty seminar page; replace `{}` with topics using the same format as Reading Notes
- topic pages link back to their section and the homepage
- each section maps topic names to topic entries
- a plain string means either one PDF title or one URL
- a list means multiple PDF titles, and the site generator will build a topic subpage
- a topic mapping can include `description`
- each file item can also include `description`
- PDF references are resolved under `docs/` by default
- PDF titles can include subfolders, such as `Etale Cohomology/Preliminaries on field theory`
- for single-PDF mappings, you can use either `file: Some Title` or `files: [Some Title]`
- PDF paths are derived automatically as `docs/title.pdf`
- if you want the page to show a different name, you can add `label: ...` to a file item
- `python3 generate_site.py build` regenerates HTML only
- `python3 generate_site.py deploy` regenerates HTML, runs `git add .`, commits with the fixed message `new content:`, pushes to `main`, and then syncs `gh-pages` from `main`

## Adding seminar notes

Put your PDF in `docs/`, then replace `Seminar Notes: {}` with, for example:

```yaml
  Seminar Notes:
    My Seminar:
      description: Notes from the seminar.
      files:
        - title: Seminar Notes/My first talk
```

This example expects `docs/Seminar Notes/My first talk.pdf`. Add more file entries for additional talks. Run `python3 generate_site.py deploy` to publish.
