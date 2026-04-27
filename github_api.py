import requests
from typing import Optional
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#2b7489",
    "C": "#555555", "C++": "#f34b7d", "Rust": "#dea584", "Go": "#00ADD8",
    "Java": "#b07219", "Ruby": "#701516", "PHP": "#4F5D95", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051", "Lua": "#000080", "Kotlin": "#F18E33",
}
def get_lang_color(lang):
    return LANG_COLORS.get(lang, "#4a9eff")
class GitHubClient:
    BASE = "https://api.github.com"
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    def test_auth(self):
        r = requests.get(f"{self.BASE}/user", headers=self.headers, timeout=10)
        if r.status_code == 200:
            return True, r.json()
        return False, r.json().get("message", "Auth failed")
    def get_repos(self, per_page=100):
        repos = []
        page = 1
        while True:
            r = requests.get(
                f"{self.BASE}/user/repos",
                headers=self.headers,
                params={"per_page": per_page, "page": page, "sort": "updated", "affiliation": "owner"},
                timeout=15
            )
            if r.status_code != 200:
                break
            data = r.json()
            if not data:
                break
            repos.extend(data)
            if len(data) < per_page:
                break
            page += 1
        return repos
    def get_repo_contents(self, owner, repo, path="", max_files=30):
        """Get file tree of a repo for AI context"""
        try:
            r = requests.get(
                f"{self.BASE}/repos/{owner}/{repo}/git/trees/HEAD",
                headers=self.headers,
                params={"recursive": "1"},
                timeout=15
            )
            if r.status_code != 200:
                return []
            tree = r.json().get("tree", [])
            files = [item["path"] for item in tree if item["type"] == "blob"]
            return files[:max_files]
        except Exception:
            return []
    def get_file_content(self, owner, repo, path):
        """Get content of a specific file"""
        try:
            r = requests.get(
                f"{self.BASE}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
                timeout=10
            )
            if r.status_code != 200:
                return None
            import base64
            content = r.json().get("content", "")
            return base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception:
            return None
    def format_repo(self, repo: dict) -> dict:
        lang = repo.get("language") or "Unknown"
        return {
            "name": repo["name"],
            "description": repo.get("description") or "",
            "github_url": repo["html_url"],
            "language": lang,
            "stars": repo.get("stargazers_count", 0),
            "color": get_lang_color(lang),
            "owner": repo["owner"]["login"],
            "full_name": repo["full_name"],
        }
