"use client";
import {useCourseReadonly} from "@/components/CourseAccess";
import { useCallback,useEffect,useState } from "react";
import { apiRequest } from "@/lib/api";
import { request } from "@/lib/lms";
import { useRealtime } from "@/components/Realtime";
import {useListPage} from "@/components/Pagination";
import ScoreCell from "@/components/ScoreCell";
type Matrix={assignments:{id:number;title:string}[];items:{student_id:string;full_name:string;scores:Record<string,number|null>;average:number|null}[]};
export default function AssignmentProgress({courseId,teacher}:{courseId:number;teacher:boolean}){
 const readonly=useCourseReadonly();
 const [data,setData]=useState<Matrix|null>(null),[error,setError]=useState("");const {revision}=useRealtime();
 const load=useCallback(async()=>setData(await apiRequest<Matrix>(`/api/courses/${courseId}/assignments/progress`)),[courseId]);
 useEffect(()=>{load().catch(e=>setError(e.message))},[load,revision]);
 useEffect(()=>{const t=setInterval(()=>void load().catch(()=>{}),5000);return()=>clearInterval(t)},[load]);
 const pagination=useListPage(data?.items.length||0);
 return <section className="panel"><h2>Tiến độ và điểm bài tập</h2><p className="section-note">{teacher&&!readonly?"Sửa từng ô, nhấn Enter hoặc chuyển ô để lưu. ":""}Trung bình tính các bài đã có điểm và bài hết hạn. Hết hạn chưa nộp tính 0; bài nộp chờ chấm để trống.</p>{error&&<p role="alert">{error}</p>}
 <div className="table-wrap"><table><thead><tr><th>Mã SV</th><th>Họ tên</th>{data?.assignments.map((a,i)=><th key={a.id} title={a.title}>{a.title.match(/^BT\d+/)?.[0]||`Bài ${i+1}`}</th>)}<th>Trung bình</th></tr></thead><tbody>{data?.items.slice(pagination.start,pagination.end).map(s=><tr key={s.student_id}><td>{s.student_id}</td><td>{s.full_name}</td>{data.assignments.map(a=><td key={a.id}>{teacher&&!readonly?<ScoreCell key={`${s.student_id}-${a.id}-${s.scores[a.id]}`} label={`${s.student_id} ${a.title}`} value={s.scores[a.id]} save={async score=>{await request(`/api/courses/${courseId}/assignments/progress`,"PATCH",{items:[{student_id:s.student_id,assignment_id:a.id,score}]});await load()}}/>:s.scores[a.id]??"—"}</td>)}<td><strong>{s.average??"—"}</strong></td></tr>)}</tbody></table></div>{pagination.controls}</section>
}
