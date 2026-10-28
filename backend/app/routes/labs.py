from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.lab import AttemptResult, LabMetadata
from app.core.sql_context import active_sql_failure
from app.labs import get_lab, list_labs
from app.learning_trace import build_learning_trace, build_input_analysis

router = APIRouter(prefix="/labs", tags=["labs"])


@router.get("", response_model=list[LabMetadata])
def get_labs() -> list[LabMetadata]:
    return [lab.metadata for lab in list_labs()]


@router.get("/{lab_id}", response_model=LabMetadata)
def get_lab_metadata(lab_id: str) -> LabMetadata:
    lab = get_lab(lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail=f"랩을 찾을 수 없습니다: {lab_id}")
    return lab.metadata


@router.post("/{lab_id}/attempt", response_model=AttemptResult)
def attempt_lab(lab_id: str, payload: dict) -> AttemptResult:
    lab = get_lab(lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail=f"랩을 찾을 수 없습니다: {lab_id}")
    result = lab.attempt(payload)
    result.learning_trace = build_learning_trace(lab_id, payload, result)
    failure = active_sql_failure()
    if failure is not None and failure.status in ('resource_limit', 'blocked'):
        result.success = False
        result.flow_nodes = result.flow_edges = result.code_snippet = None
        result.lens_steps = None
        result.lens_passed_count = 0
        result.lens_rule_id = 'resource_limit' if failure.status == 'resource_limit' else 'operation_blocked'
        result.lens_message = result.learning_trace['lens']['what']
    return result


@router.post("/{lab_id}/analyze")
def analyze_lab(lab_id: str, payload: dict) -> dict:
    if get_lab(lab_id) is None:
        raise HTTPException(status_code=404, detail=f"랩을 찾을 수 없습니다: {lab_id}")
    return build_input_analysis(lab_id, payload)


@router.get("/{lab_id}/render", response_class=HTMLResponse)
def render_lab(lab_id: str, request: Request) -> str:
    """실제 브라우저가 새로 내비게이션해서 파싱하는 원본 HTML.

    프론트엔드는 이 URL을 <iframe src="...">로 직접 로드한다 -- innerHTML
    주입이 아니라 진짜 페이지 로드이기 때문에, 취약한 랩이 반환한 <script>가
    실제로 실행된다 (DVWA와 동일한 방식).
    """
    lab = get_lab(lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail=f"랩을 찾을 수 없습니다: {lab_id}")
    if lab.render is None:
        raise HTTPException(status_code=404, detail="이 랩은 실제 렌더링을 지원하지 않습니다.")
    payload = dict(request.query_params)
    return lab.render(payload)
