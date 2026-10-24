from pathlib import Path


def test_payloadlab_uses_a_dedicated_backend_port() -> None:
    """PayloadLab must not compete with the existing localhost:8000 lab."""
    compose = (Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert '"127.0.0.1:8001:8000"' in compose
    assert "VITE_API_BASE_URL=http://localhost:8001" in compose


def test_development_ports_stay_local_and_logs_are_bounded() -> None:
    compose = (Path(__file__).resolve().parents[2] / 'docker-compose.yml').read_text(encoding='utf-8')
    assert '"127.0.0.1:8001:8000"' in compose
    assert '"127.0.0.1:5173:5173"' in compose
    assert 'max-size: "10m"' in compose
    assert 'max-file: "3"' in compose
    assert 'no-new-privileges:true' in compose
