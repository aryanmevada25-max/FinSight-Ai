import json
from pathlib import Path

from flask import Blueprint, current_app, render_template
from flask_wtf.csrf import generate_csrf


ui = Blueprint("ui", __name__, url_prefix="/app")


def vite_assets() -> tuple[str, list[str]]:
    manifest_path = Path(current_app.static_folder) / "dist" / ".vite" / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("React assets are missing. Run `npm run build` in frontend/.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["src/main.jsx"]
    return entry["file"], entry.get("css", [])


@ui.route("/", defaults={"path": ""})
@ui.route("/<path:path>")
def app(path: str):
    vite_js, vite_css = vite_assets()
    return render_template(
        "react_app.html",
        vite_js=vite_js,
        vite_css=vite_css,
        bootstrap={"csrfToken": generate_csrf(), "path": path},
    )
