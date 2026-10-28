"use client";
import { useState } from "react";
export default function ScoreCell({value,label,save}:{value:number|null;label:string;save:(value:number|null)=>Promise<void>}) {
  const [draft,setDraft]=useState(value===null?"":String(value)),[busy,setBusy]=useState(false),[error,setError]=useState("");
  async function commit(){
    if(draft===(value===null?"":String(value)))return;
    const score=draft===""?null:Number(draft);
    if(score!==null&&(!Number.isFinite(score)||score<0||score>10)){setError("Điểm từ 0 đến 10");return}
    setBusy(true);setError("");try{await save(score)}catch(e){setError(e instanceof Error?e.message:"Chưa lưu được điểm")}finally{setBusy(false)}
  }
  return <div><input className="score-input" aria-label={label} type="number" min={0} max={10} step="0.01" value={draft} disabled={busy} onChange={e=>setDraft(e.target.value)} onBlur={()=>void commit()} onKeyDown={e=>{if(e.key==="Enter"){e.preventDefault();e.currentTarget.blur()}}}/>{busy&&<small>Đang lưu…</small>}{error&&<small role="alert">{error}</small>}</div>;
}
