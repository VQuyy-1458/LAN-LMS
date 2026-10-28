"use client";
import {useEffect,useState} from "react";
import {usePathname} from "next/navigation";
import {apiRequest} from "@/lib/api";
import {type Course} from "@/lib/lms";
export const courseBranches=[["overview","Tổng quan khóa"],["students","Sinh viên"],["materials","Tài liệu"],["calendar","Lịch & Thông báo"],["attendance","Điểm danh"],["assignments","Bài tập"],["exams","Thi lập trình"],["grades","Bảng điểm"]] as const;
export default function CourseTreeNav({teacher}:{teacher:boolean}){
 const path=usePathname(),[course,setCourse]=useState<Course|null>(null),[tab,setTab]=useState("overview");
 useEffect(()=>{let live=true;const sync=()=>{
   const query=new URLSearchParams(location.search),id=Number(query.get("course"));setTab(query.get("tab")||"overview");
   if(!path.endsWith("/courses")||!id){setCourse(null);return}
   apiRequest<Course>(`/api/courses/${id}`).then(c=>{if(live)setCourse(c)}).catch(()=>{if(live)setCourse(null)});
 };sync();window.addEventListener("popstate",sync);window.addEventListener("course-navigation",sync);
 return()=>{live=false;window.removeEventListener("popstate",sync);window.removeEventListener("course-navigation",sync)}},[path]);
 if(!course)return null;
 return <div className="course-tree"><div className="tree-course">{course.course_code}<small>{course.name}</small></div>{courseBranches.filter(([k])=>teacher||k!=="students").map(([key,label])=><a key={key} className={tab===key?"active":""} aria-current={tab===key?"page":undefined} href={`/${teacher?"teacher":"student"}/courses?course=${course.id}&tab=${key}`} onClick={e=>{e.preventDefault();history.pushState(null,"",e.currentTarget.href);window.dispatchEvent(new PopStateEvent("popstate"))}}>{label}</a>)}</div>
}
