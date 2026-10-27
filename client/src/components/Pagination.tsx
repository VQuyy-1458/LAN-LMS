"use client";
import {useState,type ReactNode,Children} from "react";
export function useListPage(total:number){
 const [requested,setPage]=useState(1),pages=Math.max(1,Math.ceil(total/10)),page=Math.min(requested,pages);
 return {page,start:(page-1)*10,end:page*10,controls:<div className="actions pagination"><button className="secondary" disabled={page===1} onClick={()=>setPage(page-1)}>Trước</button><span>Trang {page}/{pages} · {total} mục</span><button className="secondary" disabled={page===pages} onClick={()=>setPage(page+1)}>Sau</button></div>};
}
export default function PaginatedList({children,className}:{children:ReactNode;className?:string}){
 const rows=Children.toArray(children),p=useListPage(rows.length);
 return <><div className={className||"stack"}>{rows.slice(p.start,p.end)}</div>{p.controls}</>;
}
