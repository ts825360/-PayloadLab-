import { it, expect } from "vitest";
import { editWindow } from "./compare-inputs.js";
it("locates an inserted connector without marking the shared suffix", () => {
  const before = "admin' '1'='1'--",
    after = "admin' OR '1'='1'--";
  const edit = editWindow(before, after);
  expect(before.slice(edit.start, edit.beforeEnd)).toBe("");
  expect(after.slice(edit.start, edit.afterEnd)).toBe("OR ");
});
it("returns an empty edit when two inputs match", () => {
  expect(editWindow("abc", "abc")).toEqual({
    start: 3,
    beforeEnd: 3,
    afterEnd: 3,
  });
});
