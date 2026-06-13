import axios from "axios";

export const API_BASE = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API_BASE, timeout: 30000 });

export async function streamChat(buddy, message, onDelta, onDone) {
  const res = await fetch(`${API_BASE}/chat/${buddy}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") { onDone?.(); return; }
      onDelta?.(data.replace(/\\n/g, "\n"));
    }
  }
  onDone?.();
}
