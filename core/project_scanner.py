from __future__ import annotations
import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FileChange:
    path: str
    change_type: str  # added, modified, deleted
    content: str = ""


@dataclass  
class ProjectContext:
    name: str
    root: str
    language: str
    files: list[str] = field(default_factory=list)
    dependencies: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)


class ProjectScanner:
    """Scan and understand project structure."""

    def __init__(self):
        self.ignore_patterns = {
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            "dist", "build", ".next", ".nuxt", "*.pyc", ".DS_Store"
        }

    def scan(self, root_path: str) -> ProjectContext:
        root = Path(root_path)
        if not root.exists():
            raise ValueError(f"Path does not exist: {root_path}")

        name = root.name
        language = self._detect_language(root)
        
        files = []
        for f in root.rglob("*"):
            if self._should_ignore(f):
                continue
            if f.is_file():
                files.append(str(f.relative_to(root)))

        dependencies = self._detect_dependencies(root, language)
        config = self._load_config(root, language)

        return ProjectContext(
            name=name,
            root=str(root),
            language=language,
            files=files[:100],  # Limit for performance
            dependencies=dependencies,
            config=config
        )

    def _detect_language(self, root: Path) -> str:
        """Detect primary language."""
        patterns = {
            "python": ["*.py", "requirements.txt", "pyproject.toml"],
            "javascript": ["*.js", "package.json"],
            "typescript": ["*.ts", "tsconfig.json"],
            "rust": ["*.rs", "Cargo.toml"],
            "go": ["*.go", "go.mod"],
            "java": ["*.java", "pom.xml"],
            "csharp": ["*.cs", "*.csproj"],
            "ruby": ["*.rb", "Gemfile"],
            "php": ["*.php", "composer.json"],
        }

        for lang, exts in patterns.items():
            for ext in exts:
                if list(root.rglob(ext)):
                    return lang
        return "unknown"

    def _detect_dependencies(self, root: Path, language: str) -> dict:
        """Detect project dependencies."""
        deps = {}
        
        if language == "python":
            for f in ["requirements.txt", "pyproject.toml", "Pipfile"]:
                if (root / f).exists():
                    deps[f] = (root / f).read_text()[:500]
        
        elif language in ("javascript", "typescript"):
            if (root / "package.json").exists():
                try:
                    pkg = json.loads((root / "package.json").read_text())
                    deps["package.json"] = pkg.get("dependencies", {})
                except Exception:
                    pass
        
        return deps

    def _load_config(self, root: Path, language: str) -> dict:
        """Load relevant config files."""
        config = {}
        
        configs = {
            "python": ["pyproject.toml", "setup.py", ".flake8", "mypy.ini"],
            "javascript": [".eslintrc", "jest.config.js", "vite.config.js"],
            "typescript": ["tsconfig.json"],
            "rust": ["Cargo.toml", "rust-toolchain"],
        }

        for cfg in configs.get(language, []):
            if (root / cfg).exists():
                try:
                    config[cfg] = (root / cfg).read_text()[:300]
                except Exception:
                    pass

        return config

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        parts = str(path).split(os.sep)
        return any(
            pattern in parts or path.name.match(pattern.replace("*", ""))
            for pattern in self.ignore_patterns
        )

    def get_file_tree(self, root_path: str, max_depth: int = 3) -> str:
        """Generate a tree view of the project."""
        root = Path(root_path)
        lines = [root.name + "/"]
        
        def walk(p: Path, prefix: str = "", depth: int = 0):
            if depth >= max_depth:
                return
            
            items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
            for i, item in enumerate(items):
                if self._should_ignore(item):
                    continue
                is_last = i == len(items) - 1
                current = "└── " if is_last else "├── "
                lines.append(prefix + current + item.name)
                if item.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    walk(item, new_prefix, depth + 1)
        
        walk(root)
        return "\n".join(lines)

    def summarize(self, root_path: str) -> str:
        """Generate a project summary."""
        ctx = self.scan(root_path)
        lines = [
            f"# Project: {ctx.name}",
            f"Language: {ctx.language}",
            f"Files: {len(ctx.files)}",
            "",
            "## Config Files"
        ]
        for cfg in ctx.config:
            lines.append(f"- {cfg}")
        
        if ctx.dependencies:
            lines.append("")
            lines.append("## Dependencies")
            for dep, _ in list(ctx.dependencies.items())[:5]:
                lines.append(f"- {dep}")
        
        return "\n".join(lines)


def get_scanner() -> ProjectScanner:
    return ProjectScanner()