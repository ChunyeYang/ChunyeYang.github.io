from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import tempfile
import textwrap
import unicodedata
from pathlib import Path
from urllib.parse import quote

import yaml


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "site.yaml"
TOPICS_DIR = ROOT / "topics"
DEPLOY_COMMIT_MESSAGE = "new content:"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "topic"


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def pdf_path_from_title(title: str) -> str:
    return f"{title}.pdf"


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


def normalize_pdf_item(item: object) -> dict[str, str | None]:
    if isinstance(item, str):
        return {"title": item, "path": pdf_path_from_title(item), "description": None}

    if not isinstance(item, dict):
        raise TypeError("Each PDF item must be a string or mapping.")

    if "title" in item:
        title = str(item["title"])
        path = str(item.get("path") or pdf_path_from_title(title))
        description = item.get("description")
        return {
            "title": title,
            "path": path,
            "description": None if description is None else str(description),
        }

    raise ValueError("Each PDF mapping must include `title`.")


def normalize_topic_entry(entry: object) -> dict[str, object]:
    if isinstance(entry, str):
        if is_url(entry):
            return {"kind": "external", "href": entry, "description": None}
        pdf = normalize_pdf_item(entry)
        return {"kind": "pdf", "files": [pdf], "description": None}

    if isinstance(entry, list):
        if len(entry) == 1 and isinstance(entry[0], str) and is_url(entry[0]):
            return {"kind": "external", "href": entry[0], "description": None}

        files = [normalize_pdf_item(item) for item in entry]
        if len(files) == 1:
            return {"kind": "pdf", "files": files, "description": None}
        return {"kind": "topic_page", "files": files, "description": None}

    if not isinstance(entry, dict):
        raise TypeError("Each topic entry must be a string, list, or mapping.")

    description = entry.get("description")
    normalized_description = None if description is None else str(description)

    if "link" in entry or "url" in entry or "external_url" in entry:
        href = str(entry.get("link") or entry.get("url") or entry.get("external_url"))
        return {"kind": "external", "href": href, "description": normalized_description}

    if "file" in entry or "pdf" in entry:
        raw_file = entry.get("file") or entry.get("pdf")
        pdf = normalize_pdf_item(raw_file)
        return {"kind": "pdf", "files": [pdf], "description": normalized_description}

    if "files" in entry or "pdfs" in entry:
        raw_files = entry.get("files") or entry.get("pdfs") or []
        files = [normalize_pdf_item(item) for item in raw_files]
        if len(files) == 1:
            return {"kind": "pdf", "files": files, "description": normalized_description}
        return {"kind": "topic_page", "files": files, "description": normalized_description}

    if "title" in entry:
        pdf = normalize_pdf_item(entry)
        return {"kind": "pdf", "files": [pdf], "description": normalized_description}

    raise ValueError("Unsupported topic entry format.")


def topic_page_filename(section_name: str, topic_name: str) -> str:
    return f"{slugify(section_name)}--{slugify(topic_name)}.html"


def load_site_data() -> dict[str, object]:
    data = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("site.yaml must define a top-level mapping.")
    if "sections" not in data:
        raise ValueError("site.yaml must include `sections`.")
    return data


def collect_referenced_pdfs(data: dict[str, object]) -> list[str]:
    pdf_paths: list[str] = []
    sections = data["sections"]
    for topics in sections.values():
        if not topics:
            continue
        for raw_topic in topics.values():
            topic = normalize_topic_entry(raw_topic)
            for file_entry in topic.get("files", []):
                pdf_paths.append(str(file_entry["path"]))
    return pdf_paths


def validate_pdf_files(pdf_paths: list[str]) -> None:
    missing = [path for path in pdf_paths if not (ROOT / path).exists()]
    if missing:
        formatted = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Referenced PDF files are missing:\n{formatted}")


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
            kind = str(topic["kind"])
            topic_description = topic.get("description")

            if kind == "external":
                href = str(topic["href"])
                link_attrs = ' target="_blank" rel="noopener"'
                meta = "Link"
            elif kind == "pdf":
                file_entry = topic["files"][0]
                href = asset_href(str(file_entry["path"]))
                link_attrs = ' target="_blank" rel="noopener"'
                meta = "PDF"
            else:
                files = topic["files"]
                href = f"topics/{topic_page_filename(str(section_name), str(topic_name))}"
                link_attrs = ""
                meta = f"{len(files)} PDFs"

            description_html = ""
            if topic_description:
                description_html = (
                    f'\n                <p class="item-description">{html.escape(str(topic_description))}</p>'
                )

            items.append(
                f"""            <li>
              <div class="topic-main">
                <div class="topic-link-row">
                  <a class="topic-link" href="{href}"{link_attrs}>{html.escape(str(topic_name))}</a>
                </div>
{description_html}
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
{chr(10).join(panels)}
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
    topic_description = topic.get("description")
    documents = []
    for file_entry in topic["files"]:
        document_description = file_entry.get("description")
        description_html = ""
        if document_description:
            description_html = (
                f'\n            <p class="item-description">{html.escape(str(document_description))}</p>'
            )

        documents.append(
            f"""          <li>
            <div class="topic-main">
              <a class="document-link" href="{asset_href(str(file_entry["path"]), "../")}" target="_blank" rel="noopener">
                {html.escape(str(file_entry["title"]))}
              </a>
{description_html}
            </div>
            <span class="document-meta">PDF</span>
          </li>"""
        )

    topic_description_html = ""
    if topic_description:
        topic_description_html = f'\n        <p class="item-description page-description">{html.escape(str(topic_description))}</p>'

    content = f"""    <main class="page">
{aside_html(name, email, "../index.html")}

      <section class="page-content">
        <p class="breadcrumbs"><a href="../index.html">Home</a> / {html.escape(section_name)}</p>
        <div class="page-title-row">
          <h2 class="page-title">{html.escape(topic_name)}</h2>
        </div>
{topic_description_html}

        <div class="panel">
          <ul class="document-list">
{chr(10).join(documents)}
          </ul>
        </div>
      </section>
    </main>"""

    return page_shell(f"{topic_name} | {name}", content, root_prefix="../")


def build_site() -> dict[str, object]:
    data = load_site_data()
    pdf_paths = collect_referenced_pdfs(data)
    validate_pdf_files(pdf_paths)

    TOPICS_DIR.mkdir(exist_ok=True)
    for old_page in TOPICS_DIR.glob("*.html"):
        old_page.unlink()

    (ROOT / "index.html").write_text(render_index(data), encoding="utf-8")

    name = str(data["name"])
    email = str(data["email"])
    sections = data["sections"]

    for section_name, topics in sections.items():
        if not topics:
            continue

        for topic_name, raw_topic in topics.items():
            topic = normalize_topic_entry(raw_topic)
            if topic["kind"] != "topic_page":
                continue

            output = TOPICS_DIR / topic_page_filename(str(section_name), str(topic_name))
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

    return data


def git(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    capture_output: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=capture_output,
    )


def build_git_env() -> tuple[dict[str, str], str | None]:
    env = os.environ.copy()
    token_file = ROOT / "token.txt"
    if not token_file.exists():
        return env, None

    remote_url = git(["remote", "get-url", "origin"], capture_output=True).stdout.strip()
    username = "git"
    match = re.search(r"github\.com[:/]([^/]+)/", remote_url)
    if match:
        username = match.group(1)

    token = token_file.read_text(encoding="utf-8").strip()
    askpass = tempfile.NamedTemporaryFile("w", delete=False, prefix="codex-askpass-", suffix=".sh")
    askpass.write(
        textwrap.dedent(
            f"""\
            #!/bin/sh
            case "$1" in
              *Username*) printf '%s\\n' '{username}' ;;
              *Password*) printf '%s\\n' '{token}' ;;
              *) printf '\\n' ;;
            esac
            """
        )
    )
    askpass.flush()
    askpass.close()
    os.chmod(askpass.name, 0o700)

    env["GIT_ASKPASS"] = askpass.name
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env, askpass.name


def deploy_site() -> None:
    build_site()
    git_env, askpass_path = build_git_env()

    try:
        git(["add", "."], env=git_env)

        diff = git(["diff", "--cached", "--quiet"], env=git_env, check=False)
        if diff.returncode not in (0, 1):
            raise subprocess.CalledProcessError(diff.returncode, diff.args)

        if diff.returncode == 1:
            git(["commit", "-m", DEPLOY_COMMIT_MESSAGE], env=git_env)

        git(["push", "origin", "main"], env=git_env)
        git(["branch", "-f", "gh-pages", "main"], env=git_env)
        git(["push", "origin", "gh-pages"], env=git_env)
    finally:
        if askpass_path:
            Path(askpass_path).unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and deploy the personal website.")
    parser.add_argument(
        "command",
        nargs="?",
        default="build",
        choices=("build", "deploy"),
        help="Use `build` to regenerate HTML only, or `deploy` to build, commit, and push.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "deploy":
        deploy_site()
        return

    build_site()


if __name__ == "__main__":
    main()
