"use client";
import { useEffect, useRef, type ReactNode } from "react";
export default function Modal({title,onClose,children}:{title:string;onClose:()=>void;children:ReactNode}) {
  const ref=useRef<HTMLDialogElement>(null);
  useEffect(()=>{const dialog=ref.current;dialog?.showModal();return()=>dialog?.close()},[]);
  return <dialog ref={ref} className="app-modal" aria-label={title} onCancel={e=>{e.preventDefault();onClose()}}>
    <div className="panel-title"><h2>{title}</h2><button className="secondary" onClick={onClose}>Đóng cửa sổ ×</button></div>{children}
  </dialog>;
}
