import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "./App.jsx";

const labs = ["sql-injection", "reflected-xss", "idor"].flatMap((id) =>
  ["easy", "medium"].map((d) => ({ id: `${id}-${d}` })),
);
const failed = {
  success: false,
  learning_trace: {
    category: "sql_injection",
    raw_input: "abc",
    effective_input: "abc",
    composition: {
      prefix: "SELECT * FROM users WHERE username = '",
      value: "abc",
      suffix: "' AND password = 'wrong'",
      full: "SELECT * FROM users WHERE username = 'abc' AND password = 'wrong'",
    },
    execution: {
      status: "empty",
      count: 0,
      error: "",
      label: "SQLite 실제 조회",
    },
    lens: {
      id: "string_value",
      title: "지금 입력은 이름이라는 값이에요",
      what: "문자열입니다.",
      why: "따옴표 안의 값입니다.",
      next: "따옴표를 확인하세요.",
      focus: { start: 0, end: 3 },
      lesson: "strings",
    },
    table: {
      columns: ["id", "username"],
      rows: [{ cells: [1, "admin"], matched: false }],
    },
    condition_tree: null,
    code: "query = username",
  },
};

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url) => ({
      ok: true,
      json: async () =>
        String(url).endsWith("/labs")
          ? labs
          : String(url).endsWith("/analyze")
            ? {
                ...structuredClone(failed.learning_trace),
                phase: "analysis",
                execution: null,
                table: null,
              }
            : structuredClone(failed),
    })),
  );
});

describe("learning workspace", () => {
  it("opens and focuses the observation stage on desktop when Enter executes the first attempt", async () => {
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
    );
    const input = screen.getByLabelText("사용자 이름");
    fireEvent.change(input, { target: { value: "박태성" } });
    input.focus();
    expect(fireEvent.keyDown(input, { key: "Enter" })).toBe(false);
    let stage = await screen.findByRole("dialog", { name: "실습 관찰 화면" });
    await waitFor(() => expect(stage).toHaveAttribute("data-view", "result"));
    expect(stage).toContainElement(document.activeElement);
    expect(input).toHaveValue("박태성");
    expect(
      fetch.mock.calls.filter(([url]) => String(url).endsWith("/attempt")),
    ).toHaveLength(1);
    for (const value of ["abc", "abc'"]) {
      fireEvent.click(screen.getByRole('button',{name:'처리 흐름과 결과 닫기'}));
      fireEvent.change(input, { target: { value } });
      input.focus();
      fireEvent.keyDown(input, { key: "Enter" });
      await waitFor(() =>
        expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
      );
      stage = await screen.findByRole('dialog',{name:'실습 관찰 화면'});
      expect(stage).toHaveAttribute("data-view", "result");
      expect(stage).toContainElement(document.activeElement);
    }
  });
  it("clears the current result when changing category without deleting saved attempts", async () => {
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
    );
    fireEvent.change(screen.getByLabelText("사용자 이름"), {
      target: { value: "abc" },
    });
    fireEvent.click(screen.getByRole("button", { name: "실행하기" }));
    await screen.findByRole('dialog',{name:'실습 관찰 화면'});
    fireEvent.click(screen.getByRole('button',{name:'처리 흐름과 결과 닫기'}));
    fireEvent.click(screen.getByRole("button", { name: /Reflected XSS/ }));
    fireEvent.click(screen.getByRole("button", { name: /SQL Injection/ }));
    expect(screen.getByLabelText("사용자 이름")).toHaveValue("");
    expect(
      screen.queryByText("지금 입력은 이름이라는 값이에요"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("table", { name: "교육용 데이터와 실제 반환 결과" }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'시도 기록 1'}));
    expect(screen.getByRole('dialog',{name:'실습 관찰 화면'})).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "시도 1 불러오기" }));
    expect(screen.getByLabelText("사용자 이름")).toHaveValue("abc");
    expect(
      await screen.findByRole("table", {
        name: "교육용 데이터와 실제 반환 결과",
      }),
    ).toBeInTheDocument();
  });
  it("keeps Lens below the input and opens focus without scrolling the page", async () => {
    const scroll = vi.fn();
    HTMLElement.prototype.scrollIntoView = scroll;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
    );
    const input = screen.getByLabelText("사용자 이름");
    fireEvent.change(input, { target: { value: "abc" } });
    await screen.findByText("지금 입력은 이름이라는 값이에요");
    expect(input.closest(".input-dock")).toContainElement(
      screen.getByRole("region", { name: "Lens 설명" }),
    );
    expect(
      fetch.mock.calls.some(([url]) => String(url).endsWith("/attempt")),
    ).toBe(false);
    expect(screen.queryByRole('dialog',{name:'실습 관찰 화면'})).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /문장에서 해당 위치 보기/ }),
    );
    expect(
      await screen.findByRole("heading", { name: "선택한 부분 자세히 보기" }),
    ).toBeInTheDocument();
    expect(screen.getByRole('dialog',{name:'실습 관찰 화면'}).querySelector('.observation-scroll').scrollTop).toBe(0);
    expect(scroll).not.toHaveBeenCalled();
    expect(input).toBeInTheDocument();
  });

  it("does not let old analysis replace a new lab", async () => {
    let respond;
    fetch.mockImplementation(async (url) =>
      String(url).endsWith("/labs")
        ? { ok: true, json: async () => labs }
        : new Promise((resolve) => {
            respond = () =>
              resolve({
                ok: true,
                json: async () => ({
                  ...failed.learning_trace,
                  phase: "analysis",
                }),
              });
          }),
    );
    render(<App />);
    fireEvent.change(screen.getByLabelText("사용자 이름"), {
      target: { value: "abc" },
    });
    await waitFor(() => expect(respond).toBeTypeOf("function"));
    fireEvent.click(screen.getByRole("button", { name: /Reflected XSS/ }));
    respond();
    await waitFor(() =>
      expect(screen.getByLabelText("검색어")).toBeInTheDocument(),
    );
    expect(
      screen.queryByText("지금 입력은 이름이라는 값이에요"),
    ).not.toBeInTheDocument();
  });
  it("opens a mobile dialog and restores its trigger on confirmed close", async () => {
    const media = vi
      .spyOn(window, "matchMedia")
      .mockImplementation((query) => ({
        matches: query.includes("max-width: 760px"),
        media: query,
        addEventListener() {},
        removeEventListener() {},
        addListener() {},
        removeListener() {},
      }));
    try {
      render(<App />);
      await waitFor(() =>
        expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
      );
      fireEvent.change(screen.getByLabelText("사용자 이름"), {
        target: { value: "abc" },
      });
      const trigger = await screen.findByRole("button", {
        name: /문장에서 해당 위치 보기/,
      });
      trigger.focus();
      fireEvent.click(trigger);
      const dialog = screen.getByRole("dialog", { name: "실습 관찰 화면" });
      expect(screen.queryByRole('region',{name:'실습 관찰 화면'})).not.toBeInTheDocument();
      const back = screen.getByRole("button", { name: "처리 흐름과 결과 닫기" });
      expect(back).toHaveFocus();
      fireEvent.keyDown(back, { key: "Tab", shiftKey: true });
      expect(dialog).toContainElement(document.activeElement);
      fireEvent.keyDown(document, { key: "Escape" });
      expect(
        screen.getByRole("alertdialog", { name: "Lens 관찰창을 닫을까요?" }),
      ).toBeInTheDocument();
      expect(dialog).toBeInTheDocument();
      fireEvent.keyDown(document, { key: "Enter", repeat: true });
      expect(dialog).toBeInTheDocument();
      fireEvent.keyDown(document, { key: "Escape" });
      expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
      expect(dialog).toBeInTheDocument();
      fireEvent.keyDown(document, { key: "Escape" });
      fireEvent.keyDown(document, { key: "Enter", isComposing: true });
      expect(dialog).toBeInTheDocument();
      fireEvent.keyDown(document, { key: "Enter" });
      expect(dialog).not.toBeInTheDocument();
      expect(screen.queryByRole('dialog',{name:'실습 관찰 화면'})).not.toBeInTheDocument();
      expect(trigger).toHaveFocus();
    } finally {
      media.mockRestore();
    }
  });
  it("keeps an editable input while the API list is unavailable", async () => {
    fetch.mockRejectedValue(new Error("offline"));
    render(<App />);
    expect(screen.getByLabelText("사용자 이름")).toBeEnabled();
    await screen.findByRole("button", { name: "연결 다시 시도" });
  });

  it("renders evidence and Lens on failed attempts, preserving it during editing", async () => {
    render(<App />);
    const run = await screen.findByRole("button", { name: "실행하기" });
    await waitFor(() => expect(run).toBeEnabled());
    const input = screen.getByLabelText("사용자 이름");
    fireEvent.change(input, { target: { value: "abc" } });
    fireEvent.click(run);
    await screen.findByRole('dialog',{name:'실습 관찰 화면'});
    fireEvent.click(screen.getByRole('button',{name:'처리 흐름과 결과 닫기'}));
    fireEvent.click(screen.getByRole('button',{name:/문장에서 해당 위치 보기/}));
    expect(
      await screen.findByRole("heading", { name: "선택한 부분 자세히 보기" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("dialog", { name: "실습 관찰 화면" }),
    ).toHaveTextContent("SQLite 실제 조회");
    fireEvent.click(screen.getByRole('button',{name:'처리 흐름과 결과 닫기'}));
    fireEvent.change(input, { target: { value: "abc'" } });
    fireEvent.click(screen.getByRole('button',{name:'시도 기록 1'}));
    expect(screen.getByRole('dialog',{name:'실습 관찰 화면'})).toHaveTextContent('SQLite 실제 조회');
    expect(
      screen.getByText("입력이 바뀌었어요. 아래는 이전 실행 결과입니다."),
    ).toBeInTheDocument();
  });

  it("uses Normal as a label while retaining the existing medium API identifier", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Normal" }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
    );
    fireEvent.change(screen.getByLabelText("사용자 이름"), {
      target: { value: "abc" },
    });
    fireEvent.click(screen.getByRole("button", { name: "실행하기" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("sql-injection-medium/attempt"),
        expect.anything(),
      ),
    );
  });

  it("rejects a late response after switching labs", async () => {
    let respond;
    fetch.mockImplementation(async (url) =>
      String(url).endsWith("/labs")
        ? { ok: true, json: async () => labs }
        : new Promise((resolve) => {
            respond = () => resolve({ ok: true, json: async () => failed });
          }),
    );
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
    );
    fireEvent.change(screen.getByLabelText("사용자 이름"), {
      target: { value: "abc" },
    });
    fireEvent.click(screen.getByRole("button", { name: "실행하기" }));
    fireEvent.click(screen.getByRole("button", { name: /Reflected XSS/ }));
    respond();
    await waitFor(() =>
      expect(screen.getByLabelText("검색어")).toBeInTheDocument(),
    );
    expect(screen.queryByText("실행한 SQL")).not.toBeInTheDocument();
  });

  it("keeps both attempts available for comparison", async () => {
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
    );
    for (const value of ["abc", "abc'"]) {
      if(screen.queryByRole('dialog',{name:'실습 관찰 화면'}))
        fireEvent.click(screen.getByRole('button',{name:'처리 흐름과 결과 닫기'}));
      fireEvent.change(screen.getByLabelText("사용자 이름"), {
        target: { value },
      });
      fireEvent.click(screen.getByRole("button", { name: "실행하기" }));
      await waitFor(() =>
        expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
      );
    }
    fireEvent.click(screen.getByRole("button", { name: "두 시도 비교" }));
    expect(
      await screen.findByRole("heading", {
        name: "어떤 수정이 결과를 바꿨을까요?",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/이전 입력/)).toBeInTheDocument();
  });

  it("explains an older backend response instead of silently hiding results", async () => {
    fetch.mockImplementation(async (url) => ({
      ok: true,
      json: async () =>
        String(url).endsWith("/labs") ? labs : { success: true },
    }));
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "실행하기" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "실행하기" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "실행 해설 데이터",
    );
  });
});
