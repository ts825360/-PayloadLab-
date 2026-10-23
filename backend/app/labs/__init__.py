from app.core.lab import Lab
from app.labs.sql_injection import sql_injection_easy, sql_injection_medium
from app.labs.reflected_xss import reflected_xss_easy, reflected_xss_medium
from app.labs.idor import idor_easy, idor_medium
from app.labs.practice_extensions import EXTENSION_LABS

REGISTRY: dict[str, Lab] = {
    lab.metadata.id: lab
    for lab in [
        sql_injection_easy,
        sql_injection_medium,
        reflected_xss_easy,
        reflected_xss_medium,
        idor_easy,
        idor_medium,
        *EXTENSION_LABS,
    ]
}


def get_lab(lab_id: str) -> Lab | None:
    return REGISTRY.get(lab_id)


def list_labs() -> list[Lab]:
    return list(REGISTRY.values())
