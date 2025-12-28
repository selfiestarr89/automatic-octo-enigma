# Automations & Pages — starter repo

This repo contains:
- `docs/index.html` — a simple static site (served by GitHub Pages).
- `scripts/check_site.py` — a small Python script that fetches a URL and writes `status.json`.
- `.github/workflows/check-site.yml` — a GitHub Actions workflow that runs the script on a schedule and commits the status file.

How to use:
1. Edit `TARGET_URL` in the GitHub Actions workflow or set it as a repository secret or environment variable.
2. Push changes. Enable Pages from branch `main` → folder: /docs
3. See Actions → run the workflow or wait for the scheduled run.
