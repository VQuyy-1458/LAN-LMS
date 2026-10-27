// The identifier selects an HttpOnly cookie; it is not an authentication token.
export function sessionTab() {
  if (typeof window === "undefined") return "";
  let id = sessionStorage.getItem("lan-lms-tab");
  if (!id) {
    id = Array.from(crypto.getRandomValues(new Uint8Array(16)), b=>b.toString(16).padStart(2,"0")).join("");
    sessionStorage.setItem("lan-lms-tab", id);
  }
  return id;
}
export function scopedUrl(path: string) {
  const url = new URL(path, window.location.origin);
  if (url.origin === window.location.origin && (url.pathname.startsWith("/api/") || url.pathname === "/ws"))
    url.searchParams.set("session_tab", sessionTab());
  return url.pathname + url.search;
}
