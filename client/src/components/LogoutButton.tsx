"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
export default function LogoutButton(){const router=useRouter();const [error,setError]=useState("");return <div><button onClick={async()=>{try{await apiRequest("/api/auth/logout",{method:"POST"});router.replace("/login");router.refresh();}catch(e){setError(e instanceof Error?e.message:"Lỗi đăng xuất");}}}>Đăng xuất</button>{error&&<p role="alert">{error}</p>}</div>;}
