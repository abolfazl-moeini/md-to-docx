import pytest


@pytest.fixture(autouse=True)
def _reset_mermaid_launch_health():
    try:
        from md_to_docx.mermaid import reset_launch_health
        reset_launch_health()
    except Exception:
        pass
    yield
    try:
        from md_to_docx.mermaid import reset_launch_health
        reset_launch_health()
    except Exception:
        pass
