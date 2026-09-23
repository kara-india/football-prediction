"""
Security Audit Test Suite — Phase 0
Scans the repository for leaked credentials, hardcoded API keys,
service role keys, and database passwords.
"""
import os
import re
import pytest

# Repository root — two levels up from this test file
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# The known compromised key pattern
LEAKED_KEY = '073534f7111a37868a403c5cd51d83fa'

# File extensions to scan
SCAN_EXTENSIONS = {
    '.ts', '.tsx', '.js', '.jsx', '.json', '.yml', '.yaml',
    '.py', '.sql', '.sh', '.css', '.html',
}

# Directories to skip entirely
SKIP_DIRS = {
    'node_modules', '.next', '.git', 'dist', '__pycache__',
    'venv', 'test_venv', '.cache', '.gemini',
}

# Files that are ALLOWED to reference the key in documentation context
# (backtick-quoted references about what to rotate, not functional code)
ALLOWED_KEY_REFERENCE_FILES = {
    'docs/DEPLOYMENT_MANUAL_STEPS.md',
    'docs/PHASE_STATUS.md',
    'docs/phases/phase_00_security_repo_hardening.md',
    'docs/MASTER_DEVELOPMENT_PLAN.md',
    'tests/test_security_audit.py',  # This test file itself
}

# Files/paths that legitimately reference SUPABASE_SERVICE_ROLE_KEY
# (server-side code, config templates, build scripts — NOT client bundles)
ALLOWED_SERVICE_KEY_FILES = {
    '.env.example',
    'scaffold.py',
    'scaffold.ps1',
    'python/config.py',
    'scripts/run_migrations.ts',
    'scripts/apply_migrations.py',
    'supabase/README.md',
    'src/lib/supabase/server.ts',  # Server-only module
}


def _collect_files(root: str, subdirs: list[str] | None = None) -> list[str]:
    """Collect all scannable files under root, optionally restricted to subdirs."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skipped directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            _, ext = os.path.splitext(fname)
            if ext in SCAN_EXTENSIONS:
                full_path = os.path.join(dirpath, fname)
                # If subdirs filter is specified, only include matching
                if subdirs:
                    rel = os.path.relpath(full_path, root).replace('\\', '/')
                    if not any(rel.startswith(sd) for sd in subdirs):
                        continue
                files.append(full_path)
    return files


def _scan_file_for_pattern(filepath: str, pattern: str) -> list[tuple[int, str]]:
    """Return list of (line_number, line_content) where pattern matches."""
    matches = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f, 1):
                if re.search(pattern, line):
                    matches.append((i, line.rstrip()))
    except (OSError, IOError):
        pass
    return matches


class TestSecurityAudit:
    """Verify no credentials or secrets are leaked in tracked repository files."""

    def test_no_leaked_api_keys_in_source_code(self):
        """Ensure the compromised API-Football key is absent from all source code files.

        Documentation files that reference the key in backtick-quoted context
        (e.g., "rotate key `073534...`") are excluded. .env.local is gitignored
        and excluded. Only functional source code is scanned.
        """
        files = _collect_files(REPO_ROOT)
        violations = []
        for fpath in files:
            rel = os.path.relpath(fpath, REPO_ROOT).replace('\\', '/')
            # Skip files that are allowed to reference the key documentarily
            if rel in ALLOWED_KEY_REFERENCE_FILES:
                continue
            hits = _scan_file_for_pattern(fpath, LEAKED_KEY)
            for line_no, content in hits:
                violations.append(f"  {rel}:{line_no}: {content}")

        assert not violations, (
            f"SECURITY VIOLATION: Found {len(violations)} leaked credential(s) in source code:\n"
            + "\n".join(violations)
        )

    def test_no_service_role_key_in_client_bundles(self):
        """Ensure SUPABASE_SERVICE_ROLE_KEY is never referenced in client-side code.

        Client-side code = src/app/ (excluding api/ routes) and src/components/.
        Server-side API routes, .env templates, and Python scripts are excluded.
        """
        # Only scan client-bundle directories
        client_files = _collect_files(REPO_ROOT, subdirs=['src/app/', 'src/components/'])
        violations = []
        for fpath in client_files:
            rel = os.path.relpath(fpath, REPO_ROOT).replace('\\', '/')
            # API routes are server-side in Next.js App Router
            if '/api/' in rel:
                continue
            hits = _scan_file_for_pattern(fpath, r'SUPABASE_SERVICE_ROLE_KEY')
            for line_no, content in hits:
                violations.append(f"  {rel}:{line_no}: {content}")

        assert not violations, (
            f"SECURITY VIOLATION: Found {len(violations)} client-side service key reference(s):\n"
            + "\n".join(violations)
        )

    def test_env_local_is_gitignored(self):
        """Verify .env.local is properly excluded by .gitignore."""
        gitignore_path = os.path.join(REPO_ROOT, '.gitignore')
        assert os.path.exists(gitignore_path), ".gitignore file is missing"

        with open(gitignore_path, 'r') as f:
            content = f.read()

        patterns = ['.env.local', '.env*.local', '*.local']
        found = any(p in content for p in patterns)
        assert found, (
            ".gitignore does not contain a pattern to exclude .env.local. "
            f"Patterns checked: {patterns}"
        )

    def test_no_hardcoded_key_fallback_in_routes(self):
        """Verify API routes don't use || 'hardcoded_key' fallback pattern."""
        api_dir = os.path.join(REPO_ROOT, 'src', 'app', 'api')
        if not os.path.exists(api_dir):
            pytest.skip("No API routes directory found")

        files = _collect_files(REPO_ROOT, subdirs=['src/app/api/'])
        # Pattern: process.env.SOMETHING || 'hex_string'
        fallback_pattern = r"process\.env\.\w+\s*\|\|\s*'[a-f0-9]{20,}'"
        violations = []
        for fpath in files:
            hits = _scan_file_for_pattern(fpath, fallback_pattern)
            for line_no, content in hits:
                rel = os.path.relpath(fpath, REPO_ROOT)
                violations.append(f"  {rel}:{line_no}: {content}")

        assert not violations, (
            f"SECURITY VIOLATION: Found {len(violations)} hardcoded key fallback(s) in API routes:\n"
            + "\n".join(violations)
        )

    def test_ci_does_not_swallow_errors(self):
        """Verify CI workflow does not use || echo to swallow errors."""
        ci_path = os.path.join(REPO_ROOT, '.github', 'workflows', 'ci.yml')
        if not os.path.exists(ci_path):
            pytest.skip("No CI workflow file found")

        with open(ci_path, 'r') as f:
            content = f.read()

        swallow_pattern = r'\|\|\s*echo\s'
        matches = re.findall(swallow_pattern, content)
        assert not matches, (
            f"CI INTEGRITY: Found {len(matches)} error-swallowing pattern(s) "
            f"('|| echo') in {ci_path}"
        )
