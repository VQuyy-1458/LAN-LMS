"use client";
import {createContext,useContext,type ReactNode} from "react";
const Readonly=createContext(false);
export const useCourseReadonly=()=>useContext(Readonly);
export default function CourseAccess({readonly,children}:{readonly:boolean;children:ReactNode}){return <Readonly.Provider value={readonly}>{children}</Readonly.Provider>}
