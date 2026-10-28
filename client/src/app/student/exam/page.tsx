"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiRequest } from "@/lib/api";
import type { Exam } from "@/lib/lms";
import ExamPlayer from "@/features/courses/ExamPlayer";
function Room() {
  const params=useSearchParams(), id=Number(params.get("exam"));
  const [exam,setExam]=useState<Exam|null>(null),[error,setError]=useState("");
  useEffect(()=>{
    let live=true;
    const load=()=>apiRequest<Exam>(`/api/coding-exams/${id}`).then(e=>{if(live)setExam(e)}).catch(e=>{if(live)setError(e.message)});
    void load(); const timer=setInterval(()=>void load(),5000);
    return()=>{live=false;clearInterval(timer)};
  },[id]);
  return <><div className="panel-title"><h1>Phòng thi lập trình</h1><span className="badge">LAN-LMS</span></div>{error&&<p role="alert">{error}</p>}{exam?<ExamPlayer exam={exam} dedicated/>:<p>Đang tải đề thi…</p>}</>;
}
export default function Page(){return <Suspense fallback={<p>Đang mở phòng thi…</p>}><Room/></Suspense>}
