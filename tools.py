import os
import subprocess
from pathlib import Path
import git

class DevOpsTools:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def list_files(self) -> list:
        """Discover repository files and structure, excluding hidden git files."""
        file_list = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip .git directory to avoid noise
            if '.git' in dirs:
                dirs.remove('.git')
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                file_list.append(rel_path)
        return file_list

    def read_file(self, path: str, max_lines: int = 200) -> str:
        """Inspect relevant source or configuration file content safely."""
        target_path = (self.repo_path / path).resolve()
        # Security check to prevent path traversal outside repo
        if not str(target_path).startswith(str(self.repo_path.resolve())):
            return "Error: Access denied. Path traversal outside repository."
        
        if not target_path.exists() or not target_path.is_file():
            return f"Error: File '{path}' not found."
        
        try:
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            if len(lines) > max_lines:
                content = "".join(lines[:max_lines])
                content += f"\n[Note: File truncated at {max_lines} lines]"
                return content
            return "".join(lines)
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def search_code(self, pattern: str) -> str:
        """Search for suspicious patterns or strings using git grep or python string matching."""
        try:
            # Try using git grep first for speed and built-in ignore support
            repo = git.Repo(self.repo_path)
            result = repo.git.grep(pattern)
            return result if result else f"No matches found for pattern: {pattern}"
        except Exception:
            # Fallback to python-based search if git grep fails
            matches = []
            for root, dirs, files in os.walk(self.repo_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for idx, line in enumerate(f, 1):
                                if pattern in line:
                                    rel = os.path.relpath(file_path, self.repo_path)
                                    matches.append(f"{rel}:{idx}: {line.strip()}")
                    except Exception:
                        continue
            return "\n".join(matches) if matches else f"No matches found for pattern: {pattern}"

    def git_log(self, max_count: int = 20) -> str:
        """Inspect recent commit history for anti-patterns or secrets in logs."""
        try:
            repo = git.Repo(self.repo_path)
            commits = list(repo.iter_commits(max_count=max_count))
            log_output = []
            for c in commits:
                log_output.append(f"Commit: {c.hexsha}\nAuthor: {c.author}\nDate: {c.committed_datetime}\nMessage: {c.summary}\n")
            return "\n".join(log_output)
        except Exception as e:
            return f"Error fetching git log: {str(e)}"