export function apiBase() {
  // If running in the browser:
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  }
  // If running on the Next.js server (inside Docker network):
  return process.env.API_INTERNAL_BASE || "http://api:8000";
}
