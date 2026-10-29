import React from "react";
import {it,expect,vi,afterEach} from "vitest";
import {render,screen,fireEvent} from "@testing-library/react";
import App from "./App.jsx";
import {attemptLab,analyzeLab,LabRequestError} from "./api.js";

afterEach(()=>vi.unstubAllGlobals());
const trace={category:"sql_injection",raw_input:"guest",effective_input:"guest",phase:"analysis",execution:null,table:null,condition_tree:null,composition:{prefix:"SELECT ",value:"guest",suffix:"",full:"SELECT guest"},lens:{id:"string_value",title:"이름 입력",what:"이름을 비교해요.",why:"문자열이에요.",next:"따옴표를 보세요.",focus:{start:0,end:5},lesson:"strings"}};
const result={success:false,learning_trace:{...trace,phase:"result",execution:{status:"empty",count:0,error:"",label:"SQLite 실제 조회"},table:{columns:["id","username"],rows:[{cells:[1,"admin"],matched:false}]}}};
function rejection(status,code,retry){
 return {ok:false,status,headers:{get:()=>retry},json:async()=>({code,detail:"SECRET_SERVER_PATH<script>"})};
}

it.each(["2","0","2<script>","99999999999999999999",undefined])("uses only a bounded numeric retry header: %s",async(retry)=>{
 vi.stubGlobal("fetch",vi.fn(async()=>rejection(429,"rate_limit",retry)));
 let error;
 try{await attemptLab("sql-injection-easy",{});}catch(e){error=e;}
 expect(error).toBeInstanceOf(LabRequestError);
 expect(error.message).toContain("요청이 잠시 몰렸습니다.");
 if(retry==="2")expect(error.message).toContain("2초 뒤");
 else expect(error.message).toContain("잠시 기다린 뒤");
 expect(error.message).not.toMatch(/SECRET|script|999999/);
});

it.each(["concurrency_limit","peer_capacity"])("explains busy service %s without inventing a time",async(code)=>{
 vi.stubGlobal("fetch",vi.fn(async()=>rejection(503,code,"2")));
 await expect(analyzeLab("sql-injection-easy",{})).rejects.toThrow("실습 서버가 사용 중입니다. 잠시 후 다시 시도해 주세요.");
});

it("keeps unknown 503 details generic",async()=>{
 vi.stubGlobal("fetch",vi.fn(async()=>rejection(503,"unknown","2")));
 await expect(attemptLab("sql-injection-easy",{})).rejects.toThrow("시도 요청이 실패했습니다");
});

it("shows an execution rate rejection and permits successful manual retry",async()=>{
 let attempts=0;
 vi.stubGlobal("fetch",vi.fn(async(url)=>{
  if(String(url).endsWith("/labs"))return {ok:true,json:async()=>[{id:"sql-injection-easy"}]};
  if(String(url).endsWith("/analyze"))return {ok:true,json:async()=>trace};
  if(++attempts===1)return rejection(429,"rate_limit","2");
  return {ok:true,json:async()=>result};
 }));
 render(<App/>);
 fireEvent.change(screen.getByLabelText("사용자 이름"),{target:{value:"guest"}});
 const run=await screen.findByRole("button",{name:"실행하기"});
 await vi.waitFor(()=>expect(run).toBeEnabled());
 fireEvent.click(run);
 expect(await screen.findByRole("alert")).toHaveTextContent("2초 뒤 다시 시도");
 expect(screen.queryByText(/SECRET/)).not.toBeInTheDocument();
 fireEvent.click(run);
 expect(await screen.findByRole("table")).toBeInTheDocument();
 expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

it("shows the automatic-analysis rate message and clears it after a new normal input",async()=>{
 let analyses=0;
 vi.stubGlobal("fetch",vi.fn(async(url)=>{
  if(String(url).endsWith("/labs"))return {ok:true,json:async()=>[{id:"sql-injection-easy"}]};
  if(++analyses===1)return rejection(429,"rate_limit","2");
  return {ok:true,json:async()=>trace};
 }));
 render(<App/>);
 const input=screen.getByLabelText("사용자 이름");
 fireEvent.change(input,{target:{value:"guest"}});
 expect(await screen.findByText(/2초 뒤 다시 시도/)).toBeInTheDocument();
 fireEvent.change(input,{target:{value:"admin"}});
 await vi.waitFor(()=>expect(screen.queryByText(/2초 뒤 다시 시도/)).not.toBeInTheDocument());
});