export type RecordRow = {
  id: string;
  version: number;
  created_at: string;
  data: any;
};
let tokenProvider: (() => Promise<string>) | null = null;
export function setTokenProvider(provider: () => Promise<string>) {
  tokenProvider = provider;
}
export async function authorizedFetch(url: string, init: RequestInit = {}) {
  const token = tokenProvider ? await tokenProvider() : null;
  return fetch(url, {
    ...init,
    headers: {
      ...init.headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
}
export async function api<T = any>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await authorizedFetch(`/api/v1${path}`, {
    ...init,
    headers: {
      ...(init.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...init.headers,
    },
  });
  const body = await response.json();
  if (!response.ok)
    throw new Error(
      typeof body.message === "string"
        ? body.message
        : Array.isArray(body.detail)
          ? body.detail.map((x: any) => x.msg).join("; ")
          : "Request failed. Please check your input.",
    );
  return body;
}
