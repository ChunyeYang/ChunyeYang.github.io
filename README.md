# ChunyeYang.github.io

Static GitHub Pages site for Chunye Yang.

## Content workflow

1. Edit `site.yaml`
2. Run `python3 generate_site.py deploy`

## YAML shape

```yaml
name: Chunye Yang
email: chunye@umich.edu

sections:
  Reading Notes:
    Etale Cohomology:
      description: Notes from a first reading seminar.
      files:
        - title: Descent theory
          description: Descent data and fpqc descent.
        - title: Etale and smooth morphisms
          description: Basic definitions and local structure.
        - title: Etale covering spaces

    Intro to Homological Algebra: Intro to Homological Algebra

    Rising Sea Notes and Exercises:
      description: Short notes and exercises.
      file: Blow-up

  Research & Publications:
    Representation stability in the (co)homology of vertical configuration spaces:
      link: https://arxiv.org/abs/xxxx.xxxxx
      description: Preprint on representation stability in vertical configuration spaces.
```

Rules:
- top-level `sections` controls homepage section order
- each section maps topic names to topic entries
- a plain string means either one PDF title or one URL
- a list means multiple PDF titles, and the site generator will build a topic subpage
- a topic mapping can include `description`
- each file item can also include `description`
- for single-PDF mappings, you can use either `file: Some Title` or `files: [Some Title]`
- PDF paths are derived automatically as `title + ".pdf"`
- `python3 generate_site.py build` regenerates HTML only
- `python3 generate_site.py deploy` regenerates HTML, runs `git add .`, commits with the fixed message `new content:`, pushes to `main`, and then syncs `gh-pages` from `main`
