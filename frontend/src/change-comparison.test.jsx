import React from "react";
import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import ChangeComparison from "./ChangeComparison.jsx";

it("keeps chronological order when comparing from the first history entry", () => {
  const history = ["abc", "abc'"].map((input, i) => ({
    id: i + 1,
    input,
    claim: "",
    result: {
      learning_trace: {
        category: "sql_injection",
        composition: { full: input },
        execution: { status: "empty", count: 0, label: "SQLite" },
        lens: { next: "다시 시도" },
      },
    },
  }));
  render(<ChangeComparison history={history} selected={history[0]} />);
  expect(screen.getByText(/이전 입력/)).toHaveTextContent("#1");
  expect(screen.getByText(/비교 입력/)).toHaveTextContent("#2");
});
