"use client";
import { useState,useEffect,type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";
export default function ChangePassword(){const router=useRouter();const [error,setError]=useState("");const [busy,setBusy]=useState(false);
 useEffect(()=>{getCurrentUser().catch(()=>router.replace("/login"));},[router]);
 async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();const form=new FormData(e.currentTarget);setError("");if(form.get("new")!==form.get("confirm")){setError("Mật khẩu xác nhận không khớp");return;}setBusy(true);try{await apiRequest("/api/auth/change-password",{method:"POST",body:JSON.stringify({current_password:form.get("current"),new_password:form.get("new")})});router.replace("/login");router.refresh();}catch(e){setError(e instanceof Error?e.message:"Không thể đổi mật khẩu");}finally{setBusy(false);}}
 return <main className="mx-auto max-w-lg p-8"><h1>Đổi mật khẩu</h1><p>Đổi mật khẩu ban đầu trước khi sử dụng hệ thống. Đổi xong cần đăng nhập lại.</p><form onSubmit={submit} className="space-y-4">{[["current","Mật khẩu hiện tại"],["new","Mật khẩu mới"],["confirm","Xác nhận mật khẩu mới"]].map(([name,label])=><label key={name} className="block">{label}<input className="block w-full rounded border p-2" type="password" name={name} required minLength={name==="current"?1:8} maxLength={128} autoComplete={name==="current"?"current-password":"new-password"}/></label>)}{error&&<p role="alert">{error}</p>}<button disabled={busy}>{busy?"Đang đổi…":"Đổi mật khẩu"}</button></form></main>;
}
