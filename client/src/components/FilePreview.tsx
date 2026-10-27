"use client";
import {useEffect,useState} from "react";
import {apiRequest} from "@/lib/api";
import {scopedUrl} from "@/lib/sessionScope";
import Modal from "./Modal";
type Preview={kind:string;text?:string;note?:string;truncated?:boolean;entries?:{name:string;size:number;readable:boolean}[]};
export default function FilePreview({id,name,onClose,kind}:{id:number;name:string;onClose:()=>void;kind?:"attachment"}){
 const base=kind==="attachment"?`/api/assignments/${id}/attachment`:`/api/assignment-submissions/${id}`;
 const [data,setData]=useState<Preview|null>(null),[entry,setEntry]=useState(""),[error,setError]=useState("");
 useEffect(()=>{let live=true;setData(null);setError("");apiRequest<Preview>(`${base}/preview${entry?`?entry=${encodeURIComponent(entry)}`:""}`).then(d=>{if(live)setData(d)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[base,entry]);
 return <Modal title={name} onClose={onClose}>{entry&&<button className="secondary" onClick={()=>setEntry("")}>← Nội dung ZIP</button>}{error&&<p role="alert">{error}</p>}{!data&&!error&&<p>Đang mở nội dung…</p>}{data?.kind==="pdf"?<iframe title={name} className="file-preview" src={scopedUrl(`${base}/view`)}/>:data?.kind==="archive"?<ul>{data.entries?.map(e=><li key={e.name}>{e.readable?<button className="ghost" onClick={()=>setEntry(e.name)}>{e.name}</button>:e.name} ({e.size} byte)</li>)}</ul>:<><p>{data?.note}</p><pre className="source-output">{data?.text}</pre>{data?.truncated&&<p>Đã rút gọn sau 2 MiB.</p>}</>}</Modal>
}
