export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Prefix for versioned API
export const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX ?? "/api/v1";

function hasDetail(x: unknown): x is { detail: unknown } {
  return typeof x === "object" && x !== null && "detail" in x;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, init);

  const data = (await res.json().catch(() => null)) as unknown;

  if (!res.ok) {
    const msg =
      hasDetail(data)
        ? String(data.detail)
        : `Request failed (${res.status})`;
    throw new Error(msg);
  }

  return data as T;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const data = (await res.json().catch(() => null)) as unknown;

  if (!res.ok) {
    const msg =
      hasDetail(data)
        ? String(data.detail)
        : `Request failed (${res.status})`;
    throw new Error(msg);
  }

  return data as T;
}
