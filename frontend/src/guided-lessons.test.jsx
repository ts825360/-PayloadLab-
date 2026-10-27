import React from "react";
import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { getLesson } from "./lesson-catalog.js";
import GuidedLesson from "./GuidedLesson.jsx";

const trace = (category, status, extra = {}) => ({
  category, phase: "execution", execution: { status }, lens: {}, ...extra,
});
const sqlPlain = trace("sql_injection", "empty", { lens: { id: "string_value" } });
const sqlMatch = trace("sql_injection", "matched", {
  raw_input: "admin' or 2=2--", effective_input: "admin' or 2=2--",
  condition_tree: { op: "OR", values: [true, true], children: [
    { id: "name", values: [true, false] }, { id: "comparison", values: [true, true] },
  ] },
  table: { rows: [{ cells: [1, "admin"], matched: true }, { cells: [2, "guest"], matched: true }] },
});
const props = (extra = {}) => ({
  lesson: getLesson("sql_injection", "easy"), stepIndex: 0,
  onAdvance: vi.fn(), onFill: vi.fn(), trace: null, result: null,
  acknowledged: false, onAcknowledge: vi.fn(), ...extra,
});

describe("guided lesson catalog", () => {
  it("starts SQL with a normal name and accepts observed empty results", () => {
    const lesson = getLesson("sql_injection", "easy");
    expect(lesson.steps[0].suggestion).toBe("admin");
    expect(lesson.steps[0].accept(sqlPlain)).toBe(true);
    expect(lesson.steps[0].accept({ ...sqlPlain, phase: "analysis" })).toBe(false);
    expect(lesson.steps[0].accept({ ...sqlPlain, execution: null })).toBe(false);
    expect(lesson.steps[0].accept({ ...sqlPlain, category: "idor" })).toBe(false);
  });
  it("treats the expected syntax error as a learning observation", () => {
    const step = getLesson("sql_injection", "easy").steps[1];
    expect(step.suggestion).toBe("admin'");
    expect(step.accept(trace("sql_injection", "syntax_error", { lens: { id: "syntax_error" } }))).toBe(true);
    expect(step.accept(sqlPlain)).toBe(false);
  });
  it("accepts equivalent SQL from trace evidence and rejects success without the guest relationship", () => {
    const step = getLesson("sql_injection", "easy").steps.at(-1);
    expect(step.accept(sqlMatch)).toBe(true);
    expect(step.accept({ ...sqlMatch, condition_tree: null })).toBe(false);
    expect(step.accept({ ...sqlMatch, table: { rows: [{ cells: [1, "admin"], matched: true }] } })).toBe(false);
    expect(step.answer).toBe("always_true");
  });
  it("provides Easy principle steps and applied Normal lessons for every available category", () => {
    for (const category of ["sql_injection", "reflected_xss", "idor", "ssrf", "command_injection", "linux_basics", "permissions"]) {
      const lesson = getLesson(category, "easy");
      expect(lesson.steps.length).toBeGreaterThanOrEqual(2);
      expect(lesson.steps.at(-1).question).toBeTruthy();
      expect(lesson.steps.at(-1).choices.some((choice) => choice.value === lesson.steps.at(-1).answer)).toBe(true);
      if (category !== "permissions") expect(getLesson(category, "medium").title).toContain("Normal · 스스로 적용하기");
    }
    expect(getLesson("permissions", "medium")).toBeNull();
    expect(getLesson("unknown", "easy")).toBeNull();
  });
  it("uses XSS recognition evidence without claiming browser execution", () => {
    const step = getLesson("reflected_xss", "easy").steps.at(-1);
    expect(step.accept(trace("reflected_xss", "recognized", { browser_execution_verified: false }))).toBe(true);
    expect(step.observation).toMatch(/실행.*검증|검증.*실행/);
    expect(step.answer).toBe("recognition_only");
  });
  it("uses the bounded extension adapters' actual tasks and paths", () => {
    expect(getLesson("linux_basics", "easy").steps[0].suggestion).toBe("ls");
    expect(getLesson("linux_basics", "medium").steps[0].suggestion).toBe("ls -l /lab");
    expect(getLesson("ssrf", "medium").steps[0].suggestion).toBe("http://preview.lab.invalid@127.0.0.1/admin");
    const steps = getLesson("permissions", "easy").steps;
    expect(steps[1].accept(trace("permissions", "command_ok", { terminal: { command: "ls -l /lab/report.txt" } }))).toBe(true);
    expect(steps[2].suggestion).toBe("cat /lab/report.txt");
  });
  it("requires ownership evidence for the own-order observation", () => {
    const step = getLesson("idor", "easy").steps[0];
    expect(step.accept(trace("idor", "own"))).toBe(false);
    expect(step.accept(trace("idor", "own", { relations: { current_user: 1042, owner: 1042 } }))).toBe(true);
  });
});

describe("GuidedLesson", () => {
  it("offers editable fill without running or advancing", () => {
    const state = props();
    render(<GuidedLesson {...state} />);
    expect(screen.getByRole("region", { name: "학습 안내" })).toBeInTheDocument();
    expect(screen.getByText(/1\s*\/\s*3/)).toBeInTheDocument();
    expect(screen.getByText("admin", { selector: "code" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "입력 예시 넣기" }));
    expect(state.onFill).toHaveBeenCalledWith("admin");
    expect(state.onAdvance).not.toHaveBeenCalled();
  });
  it("requires execution evidence and an explicit observation acknowledgement", () => {
    const state = props({ trace: sqlPlain });
    const { rerender } = render(<GuidedLesson {...state} />);
    const next = screen.getByRole("button", { name: "다음 단계" });
    expect(next).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox"));
    expect(state.onAcknowledge).toHaveBeenCalledWith(true);
    rerender(<GuidedLesson {...state} acknowledged />);
    expect(next).toBeEnabled();
    fireEvent.click(next);
    expect(state.onAdvance).toHaveBeenCalledTimes(1);
    rerender(<GuidedLesson {...state} trace={{ ...sqlPlain, phase: "analysis" }} acknowledged />);
    expect(next).toBeDisabled();
  });
  it("keeps Normal hints hidden until requested", () => {
    render(<GuidedLesson {...props({ lesson: getLesson("sql_injection", "medium") })} />);
    expect(screen.queryByRole("button", { name: "입력 예시 넣기" })).not.toBeInTheDocument();
    expect(screen.queryByText(getLesson("sql_injection", "medium").steps[0].suggestion, { selector: "code" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "단서 보기" }));
    expect(screen.getByRole("button", { name: "입력 예시 넣기" })).toBeInTheDocument();
  });
  it("requires the final understanding answer as well as observation", () => {
    const state = props({ stepIndex: 2, trace: sqlMatch, acknowledged: true });
    render(<GuidedLesson {...state} />);
    const finish = screen.getByRole("button", { name: "학습 마치기" });
    expect(finish).toBeDisabled();
    fireEvent.click(screen.getByRole("radio", { name: /guest의 이름도 admin/ }));
    expect(finish).toBeDisabled();
    fireEvent.click(screen.getByRole("radio", { name: /항상 참인 비교/ }));
    expect(finish).toBeEnabled();
    fireEvent.click(finish);
    expect(state.onAdvance).toHaveBeenCalledTimes(1);
  });
  it("clears a previous quiz selection when the step changes", () => {
    const lesson = getLesson("sql_injection", "easy");
    const state = props({ lesson, stepIndex: 2, trace: sqlMatch, acknowledged: true });
    const { rerender } = render(<GuidedLesson {...state} />);
    fireEvent.click(screen.getByRole("radio", { name: /항상 참인 비교/ }));
    rerender(<GuidedLesson {...state} stepIndex={0} />);
    rerender(<GuidedLesson {...state} />);
    expect(screen.getByRole("button", { name: "학습 마치기" })).toBeDisabled();
  });
  it("preserves the selected answer when a parent re-creates the same lesson envelope", () => {
    const state = props({ stepIndex: 2, trace: sqlMatch, acknowledged: true });
    const { rerender } = render(<GuidedLesson {...state} />);
    fireEvent.click(screen.getByRole("radio", { name: /항상 참인 비교/ }));
    rerender(<GuidedLesson {...state} lesson={getLesson("sql_injection", "easy")} />);
    expect(screen.getByRole("button", { name: "학습 마치기" })).toBeEnabled();
  });
  it("shows a completion panel only after explicit progression", () => {
    render(<GuidedLesson {...props({ stepIndex: 3 })} />);
    expect(screen.getByText("이 안내를 마쳤어요")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "다음 단계" })).not.toBeInTheDocument();
  });
});


it("accepts a supported directory listing that reveals the protected file permissions", () => {
  const fileStep = getLesson("permissions", "easy").steps.find(step => step.id === "perm-file");
  const listing = trace("permissions", "command_ok", {
    raw_input: "ls -l /lab",
    terminal: { command: "ls -l /lab", current_user: "student", files: [
      { path: "/lab/report.txt", owner: "mentor", permissions: "-rw-------" },
      { path: "/lab/readme.txt", owner: "student", permissions: "-rw-r--r--" },
    ] },
  });
  expect(fileStep.accept(listing)).toBe(true);
  expect(fileStep.accept({ ...listing, phase: "analysis" })).toBe(false);
  expect(fileStep.accept({ ...listing, raw_input: "pwd", terminal: { ...listing.terminal, command: "pwd" } })).toBe(false);
});
