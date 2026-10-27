import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";
import ts from "typescript";
const source=await readFile(new URL("../src/lib/sessionScope.ts",import.meta.url),"utf8");
const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const {sessionTab,scopedUrl}=await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
test("tab scopes persist across reload and isolate fresh tabs on HTTP LAN",()=>{
 globalThis.window={location:{origin:'http://192.168.1.100:8080'}};
 function storage(){const values=new Map();return {getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)}}
 globalThis.sessionStorage=storage();const first=sessionTab();assert.match(first,/^[a-f0-9]{32}$/);assert.equal(sessionTab(),first);
 assert.equal(scopedUrl('/api/courses/1/gradebook/export-csv'),`/api/courses/1/gradebook/export-csv?session_tab=${first}`);
 globalThis.sessionStorage=storage();assert.notEqual(sessionTab(),first);
 delete globalThis.window;delete globalThis.sessionStorage;
});
