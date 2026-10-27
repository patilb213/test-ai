
const API =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export async function api<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("test_ai_token")
      : null;

  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const message = await response.text();

    throw new Error(message || "API request failed");
  }

  return (await response.json()) as T;
}


export async function fetchEvidenceBlob(
  runId: string,
  path: string
): Promise<Blob> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("test_ai_token")
      : null;

  if (!token) {
    throw new Error("Please sign in to view evidence.");
  }

  const filename = path
    .replace(/\\/g, "/")
    .split("/")
    .pop();

  if (
    !filename ||
    !/^[a-zA-Z0-9_-]+\.png$/i.test(filename)
  ) {
    throw new Error("Invalid screenshot filename.");
  }

  const response = await fetch(
    `${API}/api/runs/${encodeURIComponent(runId)}/evidence/${encodeURIComponent(filename)}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Evidence unavailable (${response.status})`
    );
  }

  return await response.blob();
}
