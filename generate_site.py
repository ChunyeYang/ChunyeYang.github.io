from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote

import yaml


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "site.yaml"
TOPICS_DIR = ROOT / "topics"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "topic"


def asset_href(path: str, prefix: str = "") -> str:
    encoded = "/".join(quote(part, safe="._-()") for part in Path(path).parts)
    return f"{prefix}{encoded}"


def page_shell(title: str, content: str, root_prefix: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <link rel="stylesheet" href="{root_prefix}styles.css">
  </head>
  <body>
{content}
  </body>
</html>
"""


def aside_html(name: str, email: str, home_href: str) -> str:
    return f"""      <aside class="page-aside">
        <h1 class="site-name">{html.escape(name)}</h1>
        <p class="site-role">Personal Website</p>

        <div class="contact-block">
          <p class="label">Email</p>
          <p><a href="mailto:{html.escape(email)}">{html.escape(email)}</a></p>
        </div>

        <div class="contact-block">
          <p class="label">Navigation</p>
          <p><a href="{home_href}">Home</a></p>
        </div>
      </aside>"""


def normalize_file_entry(entry: object) -> dict[str, str]:
    if isinstance(entry, str):
        path = entry
        title = Path(entry).stem
        return {"title": title, "path": path}

    if not isinstance(entry, dict):
        raise TypeError("Each file entry must be a string or mapping.")

    path = entry.get("path") or entry.get("file")
    if not path:
        raise ValueError("Each file mapping must include `path`.")

    title = entry.get("title") or Path(path).stem
    return {"title": str(title), "path": str(path)}


def normalize_topic_entry(entry: object) -> dict[str, object]:
    if isinstance(entry, list):
        files = [normalize_file_entry(item) for item in entry]
        return {"files": files, "external_url": None}

    if not isinstance(entry, dict):
        raise TypeError("Each topic entry must be a list or mapping.")

    raw_files = entry.get("files", entry.get("pdfs"))
    if raw_files is None:
        raw_files = [value for key, value in entry.items() if key not in {"external_url", "external_label"}]
        if len(raw_files) == 1 and isinstance(raw_files[0], list):
            raw_files = raw_files[0]

    if raw_files is None:
        raw_files = []

    files = [normalize_file_entry(item) for item in raw_files]
    return {
        "files": files,
        "external_url": entry.get("external_url"),
        "external_label": entry.get("external_label", "External"),
    }


def topic_page_filename(section_name: str, topic_name: str) -> str:
    return f"{slugify(section_name)}--{slugify(topic_name)}.html"


def render_index(data: dict[str, object]) -> str:
    name = str(data["name"])
    email = str(data["email"])
    sections = data["sections"]

    panels: list[str] = []
    for section_name, topics in sections.items():
        if not topics:
            panels.append(
                f"""        <div class="panel">
          <h2 class="section-title">{html.escape(str(section_name))}</h2>
          <p class="section-note">Content forthcoming.</p>
        </div>"""
            )
            continue

        items: list[str] = []
        for topic_name, raw_topic in topics.items():
            topic = normalize_topic_entry(raw_topic)
            files = topic["files"]
            external_url = topic.get("external_url")
            external_label = topic.get("external_label", "External")

            if not files:
                continue

            if len(files) == 1:
                href = asset_href(files[0]["path"])
                link_attrs = ' target="_blank" rel="noopener"'
                meta = "PDF"
            else:
                href = f"topics/{topic_page_filename(section_name, topic_name)}"
                link_attrs = ""
                meta = f"{len(files)} PDFs"

            aux_link = ""
            if external_url:
                aux_link = (
                    f'<a class="aux-link" href="{html.escape(str(external_url))}" '
                    f'target="_blank" rel="noopener">{html.escape(str(external_label))}</a>'
                )

            items.append(
                f"""            <li>
              <div class="topic-main">
                <div class="topic-link-row">
                  <a class="topic-link" href="{href}"{link_attrs}>{html.escape(str(topic_name))}</a>
                  {aux_link}
                </div>
              </div>
              <span class="topic-meta">{html.escape(meta)}</span>
            </li>"""
            )

        panels.append(
            f"""        <div class="panel">
          <h2 class="section-title">{html.escape(str(section_name))}</h2>
          <ul class="topic-list">
{chr(10).join(items)}
          </ul>
        </div>"""
        )

    content = f"""    <main class="page">
{aside_html(name, email, "index.html")}

      <section class="page-content">
        <p class="intro">
          A minimal academic homepage for reading notes, research materials, and
          publications. Topic order and document order are generated directly from
          the YAML file that defines the site.
        </p>

{chr(10).join(panels)}

        <footer class="page-footer">
          Update <code>site.yaml</code> and rerun <code>python3 generate_site.py</code> to refresh the site.
        </footer>
      </section>
    </main>"""

    return page_shell(f"{name} | Personal Website", content)


def render_topic_page(
    *,
    name: str,
    email: str,
    section_name: str,
    topic_name: str,
    topic: dict[str, object],
) -> str:
    documents = []
    for file_entry in topic["files"]:
        documents.append(
            f"""          <li>
            <a class="document-link" href="{asset_href(file_entry["path"], "../")}" target="_blank" rel="noopener">
              {html.escape(file_entry["title"])}
            </a>
            <span class="document-meta">PDF</span>
          </li>"""
        )

    external_url = topic.get("external_url")
    external_html = ""
    if external_url:
        external_label = topic.get("external_label", "External")
        external_html = (
            f'<a class="aux-link" href="{html.escape(str(external_url))}" '
            f'target="_blank" rel="noopener">{html.escape(str(external_label))}</a>'
        )

    content = f"""    <main class="page">
{aside_html(name, email, "../index.html")}

      <section class="page-content">
        <p class="breadcrumbs"><a href="../index.html">Home</a> / {html.escape(section_name)}</p>
        <div class="page-title-row">
          <h2 class="page-title">{html.escape(topic_name)}</h2>
          {external_html}
        </div>

        <div class="panel">
          <ul class="document-list">
{chr(10).join(documents)}
          </ul>
        </div>

        <footer class="page-footer">
          Documents are listed in the same order as they appear in <code>site.yaml</code>.
        </footer>
      </section>
    </main>"""

    return page_shell(f"{topic_name} | {name}", content, root_prefix="../")


def main() -> None:
    data = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
    TOPICS_DIR.mkdir(exist_ok=True)

    (ROOT / "index.html").write_text(render_index(data), encoding="utf-8")

    name = str(data["name"])
    email = str(data["email"])
    sections = data["sections"]

    for section_name, topics in sections.items():
        for topic_name, raw_topic in topics.items():
            topic = normalize_topic_entry(raw_topic)
            if len(topic["files"]) <= 1:
                continue

            output = TOPICS_DIR / topic_page_filename(section_name, topic_name)
            output.write_text(
                render_topic_page(
                    name=name,
                    email=email,
                    section_name=str(section_name),
                    topic_name=str(topic_name),
                    topic=topic,
                ),
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
