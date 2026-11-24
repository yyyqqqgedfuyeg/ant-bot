"""Bootstrap black-box architecture linter for ant-bot backend."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ERROR_MSG = "[ARCH][ERROR] 禁止跨模块导入 internal，请改从对应模块的 __init__.py 导入公开契约。"


def _module_owner(path: Path, backend_root: Path) -> str | None:
    rel = path.relative_to(backend_root)
    parts = rel.parts
    if len(parts) >= 3 and parts[0] == "tools" and parts[1] == "features":
        return f"backend.tools.features.{parts[2]}"
    if len(parts) >= 2 and parts[0] in {"features", "shared"}:
        return f"backend.{parts[0]}.{parts[1]}"
    return None


def _target_owner(module_name: str) -> str | None:
    parts = module_name.split(".")
    if len(parts) >= 4 and parts[0] == "backend" and parts[1] == "tools" and parts[2] == "features":
        return ".".join(parts[:4])
    if len(parts) >= 3 and parts[0] == "backend" and parts[1] in {"features", "shared"}:
        return ".".join(parts[:3])
    return None


def check_backend_architecture(repo_root: Path | None = None) -> list[str]:
    root = repo_root or Path(__file__).resolve().parent.parent
    backend_root = root / "backend"
    if not backend_root.exists():
        return []

    errors: list[str] = []
    for py_file in sorted(backend_root.rglob("*.py")):
        owner = _module_owner(py_file, backend_root)
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            imported_modules: list[str] = []
            if isinstance(node, ast.Import):
                imported_modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules = [node.module]
            for mod in imported_modules:
                parts = mod.split(".")
                if "internal" in parts:
                    target = _target_owner(mod)
                    if target is None or target != owner:
                        errors.append(f"{py_file.relative_to(root)}:{node.lineno} {ERROR_MSG} ({mod})")
    return errors


def main() -> int:
    errors = check_backend_architecture()
    for err in errors:
        print(err, file=sys.stderr)
    if errors:
        return 1
    print("[ARCH][OK] Black-box architecture check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
