"use client";
import { useRouter } from "next/navigation";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
const Context = createContext({ status: "connecting", revision: 0 });
export const useRealtime = () => useContext(Context);
export default function Realtime({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [status, setStatus] = useState("connecting"),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    let live = true,
      socket: WebSocket | null = null,
      timer: ReturnType<typeof setTimeout> | undefined,
      attempt = 0;
    const connect = () => {
      if (!live) return;
      setStatus("connecting");
      socket = new WebSocket(
        `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws`,
      );
      socket.onopen = () => {
        attempt = 0;
        setStatus("connected");
        setRevision((v) => v + 1);
      };
      socket.onmessage = (e) => {
        try {
          const m = JSON.parse(e.data);
          if (m.type === "heartbeat")
            socket?.send(JSON.stringify({ type: "heartbeat.ack", id: m.id }));
          else setRevision((v) => v + 1);
        } catch {
          socket?.close();
        }
      };
      socket.onclose = (e) => {
        if (!live) return;
        setStatus("disconnected");
        if (e.code === 1008) {
          router.replace("/login");
          return;
        }
        timer = setTimeout(
          connect,
          Math.min(15000, 1000 * 2 ** attempt++) + Math.random() * 500,
        );
      };
      socket.onerror = () => socket?.close();
    };
    connect();
    return () => {
      live = false;
      clearTimeout(timer);
      socket?.close();
    };
  }, [router]);
  return (
    <Context.Provider value={{ status, revision }}>{children}</Context.Provider>
  );
}
export function Connection() {
  const { status } = useRealtime();
  return (
    <span className={`connection ${status}`}>
      <i />
      {status === "connected"
        ? "Đã kết nối"
        : status === "connecting"
          ? "Đang kết nối…"
          : "Mất kết nối · đang thử lại"}
    </span>
  );
}
