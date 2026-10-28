import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import useInputAnalysis from "./useInputAnalysis.js";

afterEach(() => vi.useRealTimers());

describe("input analysis requests", () => {
  it("debounces typing and never calls the attempt endpoint", async () => {
    vi.useFakeTimers();
    const fetch = vi.fn(async () => ({
      ok: true,
      json: async () => ({ phase: "analysis", execution: null }),
    }));
    vi.stubGlobal("fetch", fetch);
    const { result, rerender } = renderHook(
      ({ value }) =>
        useInputAnalysis("sql-injection-easy", { username: value }, true),
      { initialProps: { value: "a" } },
    );
    await act(() => vi.advanceTimersByTimeAsync(150));
    rerender({ value: "abc" });
    await act(() => vi.advanceTimersByTimeAsync(319));
    expect(fetch).not.toHaveBeenCalled();
    await act(() => vi.advanceTimersByTimeAsync(1));
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch.mock.calls[0][0]).toMatch(/\/analyze$/);
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      username: "abc",
    });
    expect(result.current.trace.execution).toBeNull();
  });

  it("aborts an obsolete request when the draft changes", async () => {
    vi.useFakeTimers();
    let signal;
    vi.stubGlobal(
      "fetch",
      vi.fn((_url, options) => {
        signal = options.signal;
        return new Promise(() => {});
      }),
    );
    const { result, rerender } = renderHook(
      ({ value }) =>
        useInputAnalysis("sql-injection-easy", { username: value }, true),
      { initialProps: { value: "abc" } },
    );
    await act(() => vi.advanceTimersByTimeAsync(320));
    expect(signal.aborted).toBe(false);
    rerender({ value: "next" });
    expect(signal.aborted).toBe(true);
    expect(result.current.trace).toBeNull();
    expect(result.current.status).toBe("pending");
  });
});


it('keeps safe analysis failure guidance and clears it for a new input',async()=>{
 vi.useFakeTimers();
 vi.stubGlobal('fetch',vi.fn(async()=>({ok:false,status:422})));
 const {result,rerender}=renderHook(({value})=>useInputAnalysis('sql-injection-easy',{username:value},true),{initialProps:{value:'admin'}});
 await act(()=>vi.advanceTimersByTimeAsync(320));
 expect(result.current.status).toBe('error');
 expect(result.current.error).toContain('입력 형식·길이·값이 실습 허용 범위를 벗어났습니다.');
 rerender({value:'guest'});
 expect(result.current.status).toBe('pending');
 expect(result.current.error).toBeUndefined();
 vi.unstubAllGlobals();
});
