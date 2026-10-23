import React from "react";
import { it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import ExecutionCanvas from "./ExecutionCanvas.jsx";
import { Composition, LensPanel, ConceptPanel } from "./WorkspaceParts.jsx";
import { CATEGORIES } from "./learning-content.js";

const sql = {
  category: "sql_injection",
  raw_input: "admin'OR'1'='1'--",
  effective_input: "admin'OR'1'='1'--",
  composition: {
    prefix: "SELECT * FROM users WHERE username = '",
    value: "admin'OR'1'='1'--",
    suffix: "' AND password = 'wrong'",
    ranges: {
      input: { start: 0, end: 17 },
      name: { start: 0, end: 5 },
      logic: { start: 6, end: 15 },
      comment: { start: 15, end: 17 },
    },
  },
  execution: {
    status: "matched",
    count: 2,
    error: "",
    label: "SQLite 실제 조회",
  },
  lens: {
    title: "조건 변경",
    what: "조회됐어요",
    why: "조건 비교",
    next: "다른 계정 확인",
    focus: { start: 5, end: 16 },
    lesson: "operators",
  },
  condition_tree: {
    id: "root",
    op: "OR",
    values: [true, true],
    children: [
      {
        id: "name",
        group: "name",
        text: "username = 'admin'",
        values: [true, false],
      },
      {
        id: "comparison",
        group: "logic",
        text: "'1'='1'",
        values: [true, true],
      },
    ],
  },
  table: {
    columns: ["id", "username"],
    rows: [
      { cells: [1, "admin"], matched: true },
      { cells: [2, "guest"], matched: true },
    ],
  },
};
it("changes the condition explanation when selecting a different account", () => {
  render(
    <ExecutionCanvas
      trace={sql}
      category={CATEGORIES[0]}
      labId="sql-injection-easy"
      onGroup={() => {}}
    />,
  );
  const name = screen.getByRole("button", { name: /username = 'admin'/ });
  expect(within(name.parentElement).getByText("참")).toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "guest 계정 조건 살펴보기" }),
  );
  expect(within(name.parentElement).getByText("거짓")).toBeInTheDocument();
  expect(screen.getByText("guest 계정 기준")).toBeInTheDocument();
});
it("connects the query logic segment to the condition group", () => {
  const group = vi.fn();
  render(
    <Composition
      trace={sql}
      category={CATEGORIES[0]}
      activeGroup="logic"
      onGroup={group}
      onLesson={() => {}}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "조건 부분 강조" }));
  expect(group).toHaveBeenCalledWith("logic");
});
it("does not load XSS HTML until the user explicitly opens it", () => {
  const trace = {
    raw_input: "<script></script>",
    effective_input: "<script></script>",
    execution: { status: "recognized", label: "교육용 태그 규칙" },
  };
  render(
    <ExecutionCanvas
      trace={trace}
      category={CATEGORIES[1]}
      labId="reflected-xss-easy"
    />,
  );
  expect(screen.queryByTitle("격리된 HTML 실행 결과")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "브라우저 결과 열기" }));
  expect(screen.getByTitle("격리된 HTML 실행 결과")).toHaveAttribute(
    "sandbox",
    "allow-scripts allow-modals",
  );
});
it("explains IDOR ownership instead of a SQL condition map", () => {
  const trace = {
    execution: { status: "exposed", label: "교육용 객체 조회" },
    relations: {
      current_user: 1042,
      requested_id: 1043,
      owner: 2001,
      allowed: true,
      medium: false,
    },
    table: {
      columns: ["order_id", "owner_id"],
      rows: [{ cells: [1043, 2001], matched: true }],
    },
  };
  render(<ExecutionCanvas trace={trace} category={CATEGORIES[2]} />);
  expect(screen.getByText("소유자 불일치")).toBeInTheDocument();
  expect(
    screen.getByText("서버의 소유자 확인이 빠져 있어요"),
  ).toBeInTheDocument();
});
it("reveals Normal details only when requested", () => {
  render(
    <LensPanel
      trace={sql}
      difficulty="medium"
      onFocus={() => {}}
      onLesson={() => {}}
      onRetry={() => {}}
    />,
  );
  expect(screen.queryByText("조건 비교")).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "이유와 다음 단서 펼치기 ＋" }),
  );
  expect(screen.getByText("조건 비교")).toBeInTheDocument();
});
it("focuses the concept note and supports Escape", () => {
  const close = vi.fn();
  render(<ConceptPanel lesson="operators" onClose={close} />);
  expect(screen.getByRole("button", { name: "개념 노트 닫기" })).toHaveFocus();
  fireEvent.keyDown(document, { key: "Escape" });
  expect(close).toHaveBeenCalledOnce();
});
