"use client";
import {useState} from "react";
import Modal from "./Modal";
export default function ConfirmAction({label,message,run,disabled=false}:{label:string;message:string;run:()=>Promise<void>;disabled?:boolean}){
 const [open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState("");
 return <><button type="button" className="danger" disabled={disabled} onClick={()=>{setError("");setOpen(true)}}>{label}</button>{open&&<Modal title={label} onClose={()=>{if(!busy)setOpen(false)}}><p>{message}</p>{error&&<p role="alert">{error}</p>}<div className="actions"><button disabled={busy} onClick={()=>{setBusy(true);void run().then(()=>setOpen(false)).catch(e=>setError(e.message)).finally(()=>setBusy(false))}}>Có, xác nhận</button><button className="secondary" disabled={busy} onClick={()=>setOpen(false)}>Hủy</button></div></Modal>}</>;
}
