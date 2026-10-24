// @vitest-environment node
import {it,expect} from 'vitest';
import {readFileSync} from 'node:fs';
const legacy=readFileSync(new URL('./workspace.css',import.meta.url),'utf8');
const workbench=readFileSync(new URL('./workbench.css',import.meta.url),'utf8');
const semantic=readFileSync(new URL('./theme-tokens.css',import.meta.url),'utf8');

function tokens(text){return Object.fromEntries([...text.matchAll(/--([a-z-]+):\s*(#[0-9a-fA-F]{3,6})\s*;/g)].map(([,key,value])=>[key,value]));}
function luminance(hex){let value=hex.slice(1);if(value.length===3)value=[...value].map(c=>c+c).join('');const c=value.match(/../g).map(value=>parseInt(value,16)/255).map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4);return c[0]*.2126+c[1]*.7152+c[2]*.0722;}
function contrast(a,b){const values=[luminance(a),luminance(b)].sort((a,b)=>b-a);return (values[0]+.05)/(values[1]+.05);}
it('keeps primary semantic text pairs above 4.5:1 in Light and Dark',()=>{
  const light={...tokens(legacy.split('[data-theme="dark"]')[0]),...tokens(semantic.split('[data-theme="dark"]')[0])};
  const dark={...light,...tokens(legacy.split('[data-theme="dark"]')[1].split('* {')[0]),...tokens(semantic.split('[data-theme="dark"]')[1].split('.unified-layout')[0])};
  for(const [theme,values] of [['light',light],['dark',dark]])for(const [text,background] of [['text','panel'],['muted','panel'],['input-fg','input-bg'],['button-solid-fg','button-solid'],['success-text','success-bg'],['danger-text','danger-bg'],['warning-text','warning-bg'],['info-text','info-bg'],['terminal-fg','terminal-bg'],['terminal-error','terminal-bg']]){
    expect(contrast(values[text],values[background]),`${theme}: ${text}/${background}`).toBeGreaterThanOrEqual(4.5);
  }
});

it.each(['.magnified-context','.magnifier-heading'])('keeps %s readable on the actual focus panel in both themes',(selector)=>{
  const surface=semantic.match(/[^{}]*\.focus-magnifier[^{}]*\{([^{}]*)\}/)?.[1];
  expect(surface).toMatch(/background:\s*var\(--panel\)/);
  const foreground=[...[workbench,semantic].join('\n').matchAll(/([^{}]+)\{([^{}]*)\}/g)]
    .filter(([,selectors])=>selectors.split(',').some(item=>[selector,`.unified-layout ${selector}`].includes(item.trim())))
    .map(([, ,body])=>body.match(/(?:^|;)\s*color:\s*([^;]+)/)?.[1].trim()).filter(Boolean).at(-1);
  const foregroundToken=foreground?.match(/^var\(--([a-z-]+)\)$/)?.[1];
  const light={...tokens(legacy.split('[data-theme="dark"]')[0]),...tokens(semantic.split('[data-theme="dark"]')[0])};
  const dark={...light,...tokens(legacy.split('[data-theme="dark"]')[1].split('* {')[0]),...tokens(semantic.split('[data-theme="dark"]')[1].split('.unified-layout')[0])};
  for(const [theme,values] of [['light',light],['dark',dark]]){
    expect(contrast(foregroundToken?values[foregroundToken]:foreground,values.panel),`${theme}: ${selector}/panel`).toBeGreaterThanOrEqual(4.5);
  }
  expect(foregroundToken,`${selector} uses a theme token`).toBeDefined();
});
