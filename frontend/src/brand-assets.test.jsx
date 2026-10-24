import React from 'react';
import {render,screen,fireEvent} from '@testing-library/react';
import {it,expect,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {URL as NodeURL} from 'node:url';
import App from './App.jsx';
const workbenchCss=readFileSync(new NodeURL('./workbench.css',import.meta.url),'utf8');

it('uses the approved static wordmark and selects the matching theme variant',()=>{
  localStorage.clear();
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>[{id:'sql-injection-easy'}]})));
  render(<App/>);
  const image=screen.queryByRole('img',{name:'PayloadLab'});
  expect(image).toBeInTheDocument();
  expect(image).toHaveAttribute('src','/brand/payloadlab-wordmark.svg');
  fireEvent.click(screen.getByRole('button',{name:'다크 모드로 전환'}));
  expect(image).toHaveAttribute('src','/brand/payloadlab-wordmark-dark.svg');
});

it('crops the shared wordmark to its glyph in the compact sidebar',()=>{
  const compactRules=workbenchCss.split('@media (max-width: 1250px)')[1]?.split('@media')[0] || '';
  const imageRule=compactRules.match(/\.focused-workbench \.brand > img\s*\{([^}]+)\}/)?.[1] || '';
  expect(imageRule).toMatch(/width:\s*36px/);
  expect(imageRule).toMatch(/object-fit:\s*cover/);
  expect(imageRule).toMatch(/object-position:\s*left/);
});
