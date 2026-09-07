import { isSnapshot } from "../contracts";
import type { ConsoleSnapshot, ConsoleSource, ConsoleOperation } from "./types";
export const base = (source: ConsoleSource) =>
  source === "live" ? "/console-api/v1" : "/api/v1";
export class ApiError extends Error {
  constructor(
    message: string,
    public status = 0,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export async function api<T>(
  source: ConsoleSource,
  path: string,
  body?: unknown,
  options: { key?: string; signal?: AbortSignal; method?: string } = {},
): Promise<T> {
  const response = await fetch(`${base(source)}/${path}`, {
    method: options.method ?? (body === undefined ? "GET" : "POST"),
    headers: {
      "Content-Type": "application/json",
      ...(options.key ? { "Idempotency-Key": options.key } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: options.signal
      ? AbortSignal.any([options.signal, AbortSignal.timeout(10000)])
      : AbortSignal.timeout(10000),
  });
  const value = await response.json();
  if (!response.ok)
    throw new ApiError(
      value.error?.message ??
        value.detail?.[0]?.msg ??
        `Request rejected (${response.status})`,
      response.status,
    );
  return value as T;
}
export async function state(source: ConsoleSource, signal?: AbortSignal) {
  const s = await api<ConsoleSnapshot>(
    source,
    `state?source=${source}`,
    undefined,
    { signal },
  );
  if (!isSnapshot(s) || s.source !== source)
    throw new Error(
      "Wrong or invalid data source. Controls remain unavailable.",
    );
  return s;
}
export const delay = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Cancelled", "AbortError"));
      return;
    }
    const done = () => {
      signal?.removeEventListener("abort", abort);
      resolve();
    };
    const id = setTimeout(done, ms);
    const abort = () => {
      clearTimeout(id);
      signal?.removeEventListener("abort", abort);
      reject(new DOMException("Cancelled", "AbortError"));
    };
    signal?.addEventListener("abort", abort, { once: true });
  });
export interface Intent {
  key: string;
  source: ConsoleSource;
  path: string;
  body: Record<string, unknown>;
  operation?: ConsoleOperation;
}
export function intent(
  source: ConsoleSource,
  s: ConsoleSnapshot,
  path: string,
  fields: Record<string, unknown>,
): Intent {
  return {
    key: crypto.randomUUID(),
    source,
    path,
    body: {
      run_id: s.run_id,
      source,
      expected_control_revision: s.control_revision,
      ...fields,
    },
  };
}
export async function sendIntent(
  i: Intent,
  onOperation?: (o: ConsoleOperation) => void,
  signal?: AbortSignal,
) {
  // A retry reuses the exact command and key. Never reconstruct it from a newer revision.
  let op = i.operation;
  if (!op) {
    op = await api<ConsoleOperation>(i.source, i.path, i.body, {
      key: i.key,
      signal,
    });
    i.operation = op;
    onOperation?.(op);
  }
  for (
    let count = 0;
    op.status === "queued" || op.status === "running";
    count++
  ) {
    if (count >= 30)
      throw new Error(
        "Operation is still pending. Check the same operation before sending another command.",
      );
    await delay(300, signal);
    op = await api<ConsoleOperation>(
      i.source,
      `operations/${op.operation_id}`,
      undefined,
      { signal },
    );
    i.operation = op;
    onOperation?.(op);
  }
  if (op.status !== "applied")
    throw new ApiError(op.error ?? op.message ?? `Operation ${op.status}`, 409);
  onOperation?.(op);
  return op;
}
export function subscribe(
  source: ConsoleSource,
  receive: (s: ConsoleSnapshot) => void,
  status: (s: "connecting" | "connected" | "polling" | "stale") => void,
) {
  let disposed = false,
    ws: WebSocket | null = null,
    retry: ReturnType<typeof setTimeout> | undefined,
    last = 0,
    previous: ConsoleSnapshot | null = null,
    polling = false;
  const retiredStreams = new Set<string>();
  const controller = new AbortController();
  const accept = (s: ConsoleSnapshot) => {
    if (disposed || !isSnapshot(s) || s.source !== source) return false;
    if (retiredStreams.has(s.stream_id)) return false;
    if (
      previous &&
      s.stream_id === previous.stream_id &&
      (s.run_id !== previous.run_id || s.revision <= previous.revision)
    )
      return false;
    if (previous && s.stream_id !== previous.stream_id)
      retiredStreams.add(previous.stream_id);
    previous = s;
    last = performance.now();
    receive(s);
    return true;
  };
  const poll = async () => {
    if (polling || disposed) return;
    polling = true;
    const before = previous;
    try {
      const s = await state(source, controller.signal);
      if (previous === before && accept(s)) status("polling");
    } catch {
      if (!disposed && (!last || performance.now() - last > 1500))
        status("stale");
    } finally {
      polling = false;
    }
  };
  const open = () => {
    if (disposed) return;
    status("connecting");
    const prefix = source === "live" ? "/console-ws" : "/ws";
    const sock = new WebSocket(
      `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}${prefix}/v1/state?source=${source}`,
      "truss.ui.v1",
    );
    ws = sock;
    sock.onmessage = (e) => {
      if (disposed || ws !== sock) return;
      try {
        const f = JSON.parse(e.data);
        if (f.type === "ping")
          sock.send(JSON.stringify({ type: "pong", id: f.id }));
        if (f.type === "snapshot" && accept(f.data)) status("connected");
      } catch {
        status("stale");
      }
    };
    sock.onerror = () => sock.close();
    sock.onclose = () => {
      if (disposed || ws !== sock) return;
      status("stale");
      retry = setTimeout(open, 2000);
    };
  };
  open();
  void poll();
  const timer = setInterval(() => {
    if (!last || performance.now() - last > 1500) {
      status("stale");
      void poll();
    }
  }, 750);
  return () => {
    disposed = true;
    controller.abort();
    clearInterval(timer);
    clearTimeout(retry);
    ws?.close();
  };
}
