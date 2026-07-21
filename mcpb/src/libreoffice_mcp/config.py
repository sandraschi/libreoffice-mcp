"""Settings for LibreOffice paths and extension bridge."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LIBREOFFICE_MCP_", env_file=".env")

    host: str = "127.0.0.1"
    port: int = 10981
    transport: str = "http"

    soffice_path: str = ""
    extension_bridge_url: str = "http://127.0.0.1:8765/mcp"
    templates_dir: Path = Path.home() / ".libreoffice-mcp" / "templates"
    output_dir: Path = Path.home() / ".libreoffice-mcp" / "output"
    data_dir: Path = Path.home() / ".libreoffice-mcp" / "data"
    upload_dir: Path = Path.home() / ".libreoffice-mcp" / "uploads"
    convert_timeout_sec: int = 120
    watch_poll_sec: float = 5.0
    max_upload_bytes: int = 50 * 1024 * 1024
    live_typewriter_wpm: float = 180.0
    live_max_words: int = 400
    live_calc_cell_delay_sec: float = 0.08

    central_docs_path: str = r"D:\Dev\repos\mcp-central-docs"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3.5:27b"
    lmstudio_base_url: str = "http://127.0.0.1:1234"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    def resolve_soffice(self) -> Path | None:
        if self.soffice_path:
            p = Path(self.soffice_path)
            return p if p.is_file() else None
        candidates = [
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
            Path("/usr/bin/soffice"),
            Path("/usr/bin/libreoffice"),
            Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        ]
        for c in candidates:
            if c.is_file():
                return c
        return None

    def soffice_product_version(self) -> str | None:
        """Host LibreOffice version when detectable (Windows PE metadata)."""
        exe = self.resolve_soffice()
        if exe is None:
            return None
        if exe.suffix.lower() != ".exe":
            return None
        try:
            import subprocess

            proc = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"(Get-Item -LiteralPath '{exe}').VersionInfo.ProductVersion",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            ver = (proc.stdout or "").strip()
            return ver or None
        except OSError:
            return None

    def ensure_dirs(self) -> None:
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()


def reload_settings() -> Settings:
    """Re-read .env after Settings page save."""
    global settings
    settings = Settings()
    return settings
