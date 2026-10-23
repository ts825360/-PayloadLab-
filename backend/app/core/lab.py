from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional

from pydantic import BaseModel


Difficulty = Literal["easy", "medium"]


@dataclass
class RuleCheck:
    id: str
    description: str
    check: Callable[[Any], bool]


class TableState(BaseModel):
    name: str
    columns: list[str]
    rows: list[list[str]]
    matched_row_indices: list[int] = []


class FlowNode(BaseModel):
    """One node in the code<->diagram graph shown on a successful attempt.

    `code_line` is the 0-indexed line within `SuccessDetail.code_snippet`
    this node corresponds to (None if it has no single-line home, e.g. the
    raw user input before it enters any code). The frontend uses it for
    the bidirectional hover/click highlight between the code pane and the
    node graph -- this is data the backend must supply precisely, not a
    heuristic the frontend guesses at.
    """

    id: str
    kind: Literal["input", "variable", "action", "query", "table", "result"]
    label: str
    value: str
    code_line: Optional[int] = None
    highlight: Optional[str] = None
    table: Optional[TableState] = None


class FlowEdge(BaseModel):
    source: str
    target: str


class LabMetadata(BaseModel):
    id: str
    name: str
    category: str
    difficulty: Difficulty
    route: str


class LensStep(BaseModel):
    status: Literal["passed", "failed", "unknown"]
    description: str


class SuccessDetail(BaseModel):
    flow_nodes: list[FlowNode]
    flow_edges: list[FlowEdge]
    code_snippet: Optional[str] = None


class AttemptResult(BaseModel):
    success: bool
    learning_trace: Optional[dict] = None
    flow_nodes: Optional[list[FlowNode]] = None
    flow_edges: Optional[list[FlowEdge]] = None
    code_snippet: Optional[str] = None
    lens_message: Optional[str] = None
    lens_rule_id: Optional[str] = None
    lens_passed_count: int = 0
    lens_steps: Optional[list[LensStep]] = None


@dataclass
class Lab:
    """Common lab interface, validated in issues #3/#5/#9.

    A lab supplies its own success/failure oracle via `resolve`; the shared
    `rules` chain is used only to produce the Lens diagnostic when `resolve`
    reports failure (see issue #6: this is where the real fallback lives —
    a rule's `check()` raising on malformed input, not "no rule matched",
    since the chain structurally always returns something).

    `render` is optional: labs that can demonstrate a real browser-executed
    exploit (e.g. reflected XSS) provide a function that returns a full raw
    HTML document for a given payload, served through GET /labs/{id}/render
    and loaded in a sandboxed iframe by the frontend — a real navigation, so
    <script> tags in it actually execute, unlike injecting into React's DOM.
    """

    metadata: LabMetadata
    rules: list[RuleCheck]
    resolve: Callable[[Any], tuple[bool, Optional[SuccessDetail]]]
    render: Optional[Callable[[Any], str]] = None

    def attempt(self, payload: Any) -> AttemptResult:
        try:
            success, detail = self.resolve(payload)
        except Exception:
            # resolve() itself choked on the input (e.g. wrong type for a
            # field) -- treat it the same as "resolve said no" and let
            # _diagnose's per-rule exception handling take it from here,
            # instead of a 500. This is the same #6 guarantee `_diagnose`
            # already gives for individual rule checks, extended to cover
            # resolve() too (found via #10's regression suite: resolve()
            # was the one path that could still crash the request).
            return self._diagnose(payload)
        if success:
            return AttemptResult(
                success=True,
                flow_nodes=detail.flow_nodes,
                flow_edges=detail.flow_edges,
                code_snippet=detail.code_snippet,
            )
        return self._diagnose(payload)

    def _diagnose(self, payload: Any) -> AttemptResult:
        for i, rule in enumerate(self.rules):
            try:
                passed = rule.check(payload)
            except Exception:
                return AttemptResult(
                    success=False,
                    lens_message="입력을 인식하지 못했습니다. 이 랩이 기대하는 입력 형태를 확인해보세요.",
                    lens_rule_id="fallback_unrecognized_input",
                    lens_passed_count=i,
                    lens_steps=self._lens_steps(i),
                )
            if not passed:
                return AttemptResult(
                    success=False,
                    lens_message=rule.description,
                    lens_rule_id=rule.id,
                    lens_passed_count=i,
                    lens_steps=self._lens_steps(i),
                )
        # every rule passed but resolve() still said failure: shouldn't
        # normally happen, but don't crash — surface it plainly.
        return AttemptResult(
            success=False,
            lens_message="모든 조건은 충족했지만 공격이 최종적으로 성립하지 않았습니다.",
            lens_rule_id="fallback_all_rules_passed",
            lens_passed_count=len(self.rules),
            lens_steps=self._lens_steps(len(self.rules)),
        )

    def _lens_steps(self, failed_index: int) -> list[LensStep]:
        steps = []
        for i, rule in enumerate(self.rules):
            if i < failed_index:
                status = "passed"
            elif i == failed_index:
                status = "failed"
            else:
                status = "unknown"
            steps.append(LensStep(status=status, description=rule.description))
        return steps
