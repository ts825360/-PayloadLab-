import {readFileSync} from 'node:fs';
import {CATEGORIES,labId} from '../../../frontend/src/learning-content.js';
import {PRACTICE_CONTEXT} from '../../../frontend/src/practice-context.js';
import {getLesson} from '../../../frontend/src/lesson-catalog.js';
const target=new URL('../2026-10-27-learning-flow-cases.json',import.meta.url);
if(process.argv[2]==='catalog') {
 const catalog=CATEGORIES.flatMap(c=>['easy','medium'].flatMap(d=>{
  const lesson=getLesson(c.id,d);if(!lesson)return [];
  const context=PRACTICE_CONTEXT[c.id];
  return [{id:labId(c.id,d),category:c.id,difficulty:d,field:c.field,numeric:!!c.numeric,context,goal:d==='medium'?context.normal:context.goal,lesson:{...lesson,steps:lesson.steps.map(({accept,...step})=>step)}}];
 }));
 process.stdout.write(JSON.stringify(catalog));
} else {
 const data=JSON.parse(readFileSync(target,'utf8'));
 if(data.labs.length!==13)throw Error('Expected 13 available labs');
 let count=0,probes=0,negativeChecks=0;
 for(const lab of data.labs){
  const lesson=getLesson(lab.category,lab.difficulty);
  for(const row of lab.observations){
   const step=lesson.steps.find(s=>s.id===row.step_id);
   if(!step?.accept(row.result.learning_trace,row.result))throw Error(`${lab.id}/${row.step_id}: suggestion not accepted`);
   if(step.accept(row.analysis,row.result))throw Error(`${lab.id}/${row.step_id}: analysis accepted`);
   if(step.accept({...row.result.learning_trace,category:'unrelated'},row.result))throw Error('Unrelated category accepted');
   for(const invalid of [null,{...row.result.learning_trace,execution:null},{...row.result.learning_trace,phase:'analysis'}]) {
    if(step.accept(invalid,row.result))throw Error(`${lab.id}/${row.step_id}: invalid evidence accepted`);
    negativeChecks++;
   }
   count++;
  }
  for(const row of lab.probes || []) {
   const step=lesson.steps.find(s=>s.id===row.step_id);
   if(step.accept(row.result.learning_trace,row.result)!==row.expected_accept)throw Error(`${lab.id}/${row.step_id}: control mismatch ${JSON.stringify(row.payload)}`);
   if(step.accept(row.analysis,row.result))throw Error('Control analysis accepted');
   probes++;
  }
 }
 console.log(`13 labs / ${count} actual route observations accepted; pending analysis and unrelated category rejected; ${negativeChecks} invalid-evidence checks and ${probes} real-input controls passed. permissions Normal has no lesson.`);
 if(getLesson('permissions','medium')!==null)throw Error('permissions Normal unexpectedly offered');
}
