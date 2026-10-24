import React, { createRef } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import InputDock from "./InputDock.jsx";

function setup(overrides = {}) {
  const onRun = vi.fn((e) => e.preventDefault());
  render(
    <InputDock
      category={{ short: "SQL", fieldLabel: "사용자 이름", field: "username" }}
      difficulty="easy"
      input="abc"
      claim=""
      onInput={() => {}}
      onRun={onRun}
      inputRef={createRef()}
      available={true}
      {...overrides}
    />,
  );
  return { input: screen.getByLabelText(overrides.category?.fieldLabel || "사용자 이름"), onRun };
}

it("submits on Enter and reserves Shift+Enter for the native newline", () => {
  const { input, onRun } = setup();
  expect(fireEvent.keyDown(input, { key: "Enter", shiftKey: true })).toBe(true);
  expect(onRun).not.toHaveBeenCalled();
  expect(fireEvent.keyDown(input, { key: "Enter" })).toBe(false);
  expect(onRun).toHaveBeenCalledTimes(1);
});

it("does not execute while composing Korean text or holding Enter", () => {
  const { input, onRun } = setup();
  fireEvent.compositionStart(input);
  fireEvent.keyDown(input, { key: "Enter" });
  fireEvent.compositionEnd(input);
  fireEvent.keyDown(input, { key: "Enter", keyCode: 229 });
  fireEvent.keyDown(input, { key: "Enter", isComposing: true });
  fireEvent.keyDown(input, { key: "Enter", repeat: true });
  expect(onRun).not.toHaveBeenCalled();
  fireEvent.keyDown(input, { key: "Enter" });
  expect(onRun).toHaveBeenCalledTimes(1);
});

it("does not submit from the shortcut while execution is busy", () => {
  const { input, onRun } = setup({ busy: true });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(onRun).not.toHaveBeenCalled();
});

it('starts a web input on the same compact first line as its ASCII prompt',()=>{
  const {input}=setup();
  expect(screen.getByText('>',{selector:'.editor-prompt'})).toBeInTheDocument();
  expect(input.style.height).toBe('24px');
});

it('keeps native Enter, Shift+Enter and Korean composition in the terminal input',()=>{
  const {input,onRun}=setup({category:{id:'permissions',short:'PERM',terminal:true,fieldLabel:'터미널 명령어',field:'command'}});
  expect(screen.getByLabelText('가상 터미널 프롬프트')).toHaveTextContent('student@practice:/lab$');
  expect(input.closest('.terminal-input-row')).not.toBeNull();
  expect(fireEvent.keyDown(input,{key:'Enter',shiftKey:true})).toBe(true);
  fireEvent.compositionStart(input);
  fireEvent.keyDown(input,{key:'Enter'});
  fireEvent.compositionEnd(input);
  fireEvent.keyDown(input,{key:'Enter',isComposing:true});
  fireEvent.keyDown(input,{key:'Enter',keyCode:229});
  fireEvent.keyDown(input,{key:'Enter',repeat:true});
  expect(onRun).not.toHaveBeenCalled();
  fireEvent.keyDown(input,{key:'Enter'});
  expect(onRun).toHaveBeenCalledTimes(1);
});
