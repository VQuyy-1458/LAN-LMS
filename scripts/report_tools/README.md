# Report renderer

`render_docx.py` is the Codex document renderer supplied by OpenAI (runtime bundle 26.1024.11018), retained to reproduce document layout checks. It is a supporting tool, not a technical contribution claimed by the student team.

The report CI job uses LibreOffice and Poppler on an isolated Ubuntu runner, as explicitly selected by the project owner after Word PDF export failed on Windows. It exports the committed DOCX to PDF and page PNGs. If Times New Roman is unavailable, the runner uses its installed serif font substitution; verify the final DOCX again on the actual submission machine after editing group information.

The CI artifact is for layout review. A successful command alone does not mean all page images have been visually reviewed.
