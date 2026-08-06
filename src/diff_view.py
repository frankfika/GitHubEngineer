"""Unified-diff parser used by the web UI's CodeMirror 6 diff view.

The web UI's diff view consumes a single ``{"files": [...]}`` envelope;
each file carries a list of hunks with the metadata the prototype's
``paintAllLines`` / sidebar cards need (header, old/new start, counts,
body text, line type). Keeping this in its own module lets the HTTP
endpoint stay a one-liner and makes the parser unit-testable in
isolation.

The parser follows the conventions of ``git diff`` output:

* file header: ``diff --git a/<path> b/<path>`` followed by
  ``--- a/<path>`` and ``+++ b/<path>``;
* hunk header: ``@@ -<old_start>,<old_count> +<new_start>,<new_count> @@``;
* body lines: leading `` `` (context), ``+`` (add), ``-`` (remove).

Output shape (matches the prototype's inlined JSON; see
``dist/prototypes/diff-codemirror/index.html``):

    {
      "files": [
        {
          "path": "src/repair_worker.py",
          "hunks": [
            {
              "id": 0,
              "header": "@@ -58,6 +58,60 @@",
              "old_start": 58, "old_lines": 6,
              "new_start": 58, "new_lines": 60,
              "lines": [
                {"type": "context", "text": "    atomic_write_json(path, job)"},
                {"type": "add",     "text": "def run_with_retry("},
                ...
              ]
            }
          ]
        }
      ]
    }

The hunk ``id`` is a **global** index across all files so the
CodeMirror sidebar can number cards consistently (``Hunks · 6``) and
the accept/reject POSTs can refer to hunks by a single integer.
"""

from __future__ import annotations

import re
import shlex
from typing import Any

# ``git diff`` hunks use ``@@ -<old>[,<old_count>] +<new>[,<new_count>] @@``.
# Counts are optional in the spec; ``git diff`` always emits them, but
# third-party tooling may omit them — in which case the count defaults
# to 1 line.
_HUNK_HEADER_RE = re.compile(
    r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@"
)


def _parse_hunk_header(line: str) -> tuple[int, int, int, int] | None:
    """Return ``(old_start, old_lines, new_start, new_lines)`` or ``None``."""

    match = _HUNK_HEADER_RE.match(line)
    if match is None:
        return None
    return (
        int(match.group(1)),
        int(match.group(2)) if match.group(2) is not None else 1,
        int(match.group(3)),
        int(match.group(4)) if match.group(4) is not None else 1,
    )


def parse_unified_diff(text: str) -> dict[str, list[dict[str, Any]]]:
    """Parse a unified-diff string into the ``{"files": [...]}`` envelope.

    The parser is intentionally tolerant: malformed hunks are skipped
    rather than raising, so a partial diff (e.g. the worker was killed
    mid-write) still renders a best-effort view in the UI.
    """

    files: list[dict[str, Any]] = []
    current_file: dict[str, Any] | None = None
    current_hunk: dict[str, Any] | None = None
    hunk_id = 0

    for raw_line in text.splitlines():
        if raw_line.startswith("diff --git "):
            # ``diff --git a/foo b/foo`` — both sides usually agree, but
            # if they differ (e.g. rename) we surface the post-image name
            # which is what ``git apply`` would create.
            current_file = {"path": _extract_path_from_diff_header(raw_line), "hunks": []}
            files.append(current_file)
            current_hunk = None
            continue
        if raw_line.startswith("--- ") or raw_line.startswith("+++ "):
            # File-aux header. The ``+++`` line carries the canonical
            # post-image path; we overwrite the placeholder set by
            # ``diff --git`` so renames show the new name.
            if current_file is not None and raw_line.startswith("+++ "):
                path = _decode_git_path(raw_line[4:].strip())
                if path != "/dev/null":
                    current_file["path"] = path
            continue
        if raw_line.startswith("@@"):
            header = _parse_hunk_header(raw_line)
            if header is None or current_file is None:
                current_hunk = None
                continue
            old_start, old_lines, new_start, new_lines = header
            current_hunk = {
                "id": hunk_id,
                "header": raw_line,
                "old_start": old_start,
                "old_lines": old_lines,
                "new_start": new_start,
                "new_lines": new_lines,
                "lines": [],
            }
            current_file["hunks"].append(current_hunk)
            hunk_id += 1
            continue
        if current_hunk is None:
            # Lines before the first hunk (e.g. ``index 1234..5678``)
            # carry no content for the UI; skip them silently.
            continue
        if raw_line.startswith("+"):
            current_hunk["lines"].append({"type": "add", "text": raw_line[1:]})
        elif raw_line.startswith("-"):
            current_hunk["lines"].append({"type": "remove", "text": raw_line[1:]})
        elif raw_line.startswith(" "):
            current_hunk["lines"].append({"type": "context", "text": raw_line[1:]})
        elif raw_line.startswith("\\"):
            # "\ No newline at end of file" — pure metadata, drop.
            continue
        else:
            # End of hunk (next file or non-diff text). Close the current
            # hunk and treat the line as a new file header if it begins
            # with ``diff``.
            current_hunk = None

    return {"files": files}


def _extract_path_from_diff_header(line: str) -> str:
    """Best-effort path extraction from a ``diff --git`` header.

    Handles renames of the form ``diff --git a/foo b/bar`` where the
    post-image path differs. Falls back to the first path-like token
    when the line does not match the canonical shape.
    """

    stripped = line[len("diff --git "):].strip()
    if not stripped.startswith('"') and " b/" in stripped:
        return stripped.rsplit(" b/", 1)[1]
    try:
        paths = shlex.split(stripped)
    except ValueError:
        paths = stripped.split()
    candidate = paths[1] if len(paths) >= 2 else (paths[0] if paths else "")
    return candidate[2:] if candidate.startswith("b/") else candidate


def _decode_git_path(value: str) -> str:
    """Decode one path from a ``---``/``+++`` header."""

    if value == "/dev/null":
        return value
    if value.startswith('"'):
        try:
            parts = shlex.split(value)
        except ValueError:
            parts = [value]
        candidate = parts[0] if parts else value
    else:
        # A timestamp, when present, is tab-delimited. Spaces before that
        # tab are part of the path and must not be tokenized.
        candidate = value.split("\t", 1)[0]
    return candidate[2:] if candidate.startswith(("a/", "b/")) else candidate


def summarise_diff(parsed: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    """Aggregate counts for the diff view's header strip.

    Returns ``{"files": N, "hunks": N, "adds": N, "rems": N}`` for the
    prototype's ``meta-stats`` row. The function is tolerant of empty
    input — a diff that produced no hunks still returns zeros rather
    than raising.
    """

    files = parsed.get("files") or []
    total_hunks = 0
    total_adds = 0
    total_rems = 0
    for file_entry in files:
        for hunk in file_entry.get("hunks") or []:
            total_hunks += 1
            for line in hunk.get("lines") or []:
                if line.get("type") == "add":
                    total_adds += 1
                elif line.get("type") == "remove":
                    total_rems += 1
    return {
        "files": len(files),
        "hunks": total_hunks,
        "adds": total_adds,
        "rems": total_rems,
    }


def select_unified_diff_hunks(text: str, accepted_ids: set[int]) -> tuple[str, int, int]:
    """Return a patch containing only the selected global hunk IDs.

    File headers and extended metadata are retained only for files with at
    least one selected hunk.  The IDs use the same global, zero-based ordering
    as :func:`parse_unified_diff`.

    The final two return values are ``(total_hunks, header_only_files)``.
    ``header_only_files`` counts diff sections which cannot be represented by
    hunk decisions (for example a pure rename, mode-only change, or binary
    patch).  Callers should fail closed when that value is non-zero.
    """

    sections: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            current = [line]
            sections.append(current)
        elif current is not None:
            current.append(line)

    selected_sections: list[str] = []
    next_hunk_id = 0
    header_only_files = 0
    for section in sections:
        first_hunk = next(
            (index for index, line in enumerate(section) if line.startswith("@@")),
            None,
        )
        if first_hunk is None:
            # A normal textual file diff always has a hunk.  Any non-empty
            # diff section without one needs an all-or-nothing review model,
            # which this UI does not currently expose.
            header_only_files += 1
            continue

        preamble = section[:first_hunk]
        if any(
            line.startswith(
                ("rename from ", "rename to ", "similarity index ", "dissimilarity index ")
            )
            for line in preamble
        ):
            header_only_files += 1
            next_hunk_id += sum(1 for line in section if line.startswith("@@"))
            continue
        # Permission metadata is not represented in the review UI. Exclude it
        # from accepted textual patches rather than silently committing it.
        preamble = [
            line
            for line in preamble
            if not line.startswith(("old mode ", "new mode "))
        ]
        selected_body: list[str] = []
        index = first_hunk
        while index < len(section):
            if not section[index].startswith("@@"):
                index += 1
                continue
            end = index + 1
            while end < len(section) and not section[end].startswith("@@"):
                end += 1
            if next_hunk_id in accepted_ids:
                selected_body.extend(section[index:end])
            next_hunk_id += 1
            index = end
        if selected_body:
            selected_sections.append("".join([*preamble, *selected_body]))

    patch = "".join(selected_sections)
    if patch and not patch.endswith("\n"):
        patch += "\n"
    return patch, next_hunk_id, header_only_files
