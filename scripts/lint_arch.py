"""Black-box architecture linter for ant-bot backend."""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Sequence
from pathlib import Path

ERROR_MSG = "[ARCH][ERROR] 禁止跨模块导入 internal，请改从对应模块的 __init__.py 导入公开契约。"
ALL_ERROR_MSG = "[ARCH][ERROR] 模块公开入口 __init__.py 必须显式声明 __all__。"

_MODULE_PARENT_DIRS: tuple[Path, ...] = (
    Path("features"),
    Path("tools") / "features",
    Path("shared"),
)


def _module_owner(path: Path, backend_root: Path) -> str | None:
    rel = path.relative_to(backend_root)
    parts = rel.parts
    if len(parts) >= 4 and parts[0] == "tools" and parts[1] == "features":
        if not parts[2].endswith(".py"):
            return f"backend.tools.features.{parts[2]}"
        return None
    if len(parts) >= 3 and parts[0] in {"features", "shared"}:
        if not parts[1].endswith(".py"):
            return f"backend.{parts[0]}.{parts[1]}"
        return None
    return None


def _target_owner(module_name: str) -> str | None:
    parts = module_name.split(".")
    if len(parts) >= 4 and parts[0] == "backend" and parts[1] == "tools" and parts[2] == "features":
        return ".".join(parts[:4])
    if len(parts) >= 3 and parts[0] == "backend" and parts[1] in {"features", "shared"}:
        return ".".join(parts[:3])
    return None


def _is_cross_module_internal(module_name: str, caller_owner: str | None) -> bool:
    parts = module_name.split(".")
    if not parts or parts[0] != "backend" or "internal" not in parts:
        return False
    target = _target_owner(module_name)
    return target is None or target != caller_owner


def _resolve_import_from(
    node: ast.ImportFrom,
    file_path: Path,
    backend_root: Path,
) -> tuple[str, list[str], bool]:
    """Return (base_module, full_alias_targets, escaped_backend_root)."""
    alias_names = [alias.name for alias in node.names if alias.name != "*"]
    if node.level == 0:
        base = node.module or ""
        full_targets = [f"{base}.{name}" if base else name for name in alias_names]
        return base, full_targets, False

    rel = file_path.relative_to(backend_root)
    package_parts = ["backend", *rel.parts[:-1]]
    up = node.level - 1
    if up > len(package_parts):
        base = node.module or ""
        full_targets = [f"{base}.{name}" if base else name for name in alias_names]
        return base, full_targets, True

    base_parts = package_parts[: len(package_parts) - up]
    mod_parts = node.module.split(".") if node.module else []
    resolved_base = ".".join([*base_parts, *mod_parts])
    full_targets = [
        f"{resolved_base}.{name}" if resolved_base else name for name in alias_names
    ]
    return resolved_base, full_targets, False


def check_source_imports(
    source: str,
    file_path: Path,
    backend_root: Path,
    repo_root: Path | None = None,
) -> list[str]:
    """Check a Python source snippet/file under backend_root for internal import violations."""
    root = repo_root or backend_root.parent
    owner = _module_owner(file_path, backend_root)
    tree = ast.parse(source, filename=str(file_path))
    display_path = file_path.relative_to(root) if file_path.is_relative_to(root) else file_path
    errors: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_cross_module_internal(alias.name, owner):
                    errors.append(f"{display_path}:{node.lineno} {ERROR_MSG} ({alias.name})")
        elif isinstance(node, ast.ImportFrom):
            base_mod, alias_targets, escaped = _resolve_import_from(node, file_path, backend_root)
            if escaped:
                raw_candidates = [base_mod, *alias_targets] if base_mod else alias_targets
                for cand in raw_candidates:
                    if "internal" in cand.split("."):
                        errors.append(f"{display_path}:{node.lineno} {ERROR_MSG} ({cand})")
                        break
                continue

            if base_mod and _is_cross_module_internal(base_mod, owner):
                errors.append(f"{display_path}:{node.lineno} {ERROR_MSG} ({base_mod})")
                continue

            for target_mod in alias_targets:
                if _is_cross_module_internal(target_mod, owner):
                    errors.append(f"{display_path}:{node.lineno} {ERROR_MSG} ({target_mod})")
                    break

    return errors


def _has_explicit_dunder_all(tree: ast.Module) -> bool:
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return not (isinstance(stmt.value, ast.Constant) and stmt.value.value is None)
        elif (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.target.id == "__all__"
            and stmt.value is not None
        ):
            return not (isinstance(stmt.value, ast.Constant) and stmt.value.value is None)
    return False


def check_init_all(init_file: Path, repo_root: Path | None = None) -> list[str]:
    """Validate that a module's __init__.py explicitly declares __all__."""
    source = init_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(init_file))
    if _has_explicit_dunder_all(tree):
        return []
    display_path = (
        init_file.relative_to(repo_root)
        if repo_root is not None and init_file.is_relative_to(repo_root)
        else init_file
    )
    return [f"{display_path}:1 {ALL_ERROR_MSG}"]


def check_backend_architecture(repo_root: Path | None = None) -> list[str]:
    """Scan backend/ for cross-module internal imports and missing __all__ declarations."""
    root = (repo_root or Path(__file__).resolve().parent.parent).resolve()
    backend_root = root / "backend"
    if not backend_root.exists():
        return []

    errors: list[str] = []
    for py_file in sorted(backend_root.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        errors.extend(
            check_source_imports(
                py_file.read_text(encoding="utf-8"),
                file_path=py_file,
                backend_root=backend_root,
                repo_root=root,
            )
        )

    for parent_rel in _MODULE_PARENT_DIRS:
        parent_dir = backend_root / parent_rel
        if not parent_dir.is_dir():
            continue
        for mod_dir in sorted(parent_dir.iterdir()):
            if not mod_dir.is_dir() or mod_dir.name.startswith(("__", ".")):
                continue
            init_file = mod_dir / "__init__.py"
            if not init_file.exists():
                if any(
                    "__pycache__" not in p.parts for p in mod_dir.rglob("*.py")
                ):
                    errors.append(f"{mod_dir.relative_to(root)}/__init__.py:1 {ALL_ERROR_MSG}")
                continue
            errors.extend(check_init_all(init_file, repo_root=root))

    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate black-box architecture rules.")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root directory to scan (defaults to project root).",
    )
    args = parser.parse_args(argv)
    errors = check_backend_architecture(repo_root=args.root)
    for err in errors:
        print(err, file=sys.stderr)
    if errors:
        return 1
    print("[ARCH][OK] Black-box architecture check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
