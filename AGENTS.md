# Agent Guidelines

- Use `uv` for dependency and environment management (`uv sync`, `uv add`, `uv run`).
- Use `prek` for repo checks (`uv run prek run --all-files`) before submitting changes.
- Keep Python code typed and `ty`-clean (`uv run ty check`).
- Prefer running the app via package entry points: `ortho-remote` or `orm`.
