import { useEffect, useRef, useState } from "react";
import type {
  ConsoleSnapshot,
  ConsoleSource,
  Fairness,
  HistoryPoint,
  Runtime,
  ConsoleOperation,
} from "./types";
import {
  api,
  ApiError,
  intent,
  sendIntent,
  state,
  subscribe,
  type Intent,
} from "./transport";
import { historyPoint } from "./model";
export function useConsole() {
  const [source, updateSource] = useState<ConsoleSource>("live");
  const [snapshot, setSnapshot] = useState<ConsoleSnapshot | null>(null);
  const [connection, setConnection] = useState<
    "connecting" | "connected" | "polling" | "stale"
  >("connecting");
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [runtime, setRuntime] = useState<Runtime | null>(null);
  const [fairness, setFairness] = useState<Fairness | null>(null);
  const [auxError, setAuxError] = useState("");
  const [busy, updateBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [operation, setOperation] = useState<ConsoleOperation | null>(null);
  const [unresolved, setUnresolved] = useState<Intent | null>(null);
  const latest = useRef<ConsoleSnapshot | null>(null);
  const alive = useRef(true);
  const busyRef = useRef(false);
  const pendingIntent = useRef<Intent | null>(null);
  const setBusy = (value: boolean) => {
    busyRef.current = value;
    if (alive.current) updateBusy(value);
  };
  const setSource = (value: ConsoleSource) => {
    if (!busyRef.current && !pendingIntent.current) updateSource(value);
  };
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    setSnapshot(null);
    latest.current = null;
    setHistory([]);
    setRuntime(null);
    setFairness(null);
    setMessage("");
    setAuxError("");
    setOperation(null);
    setConnection("connecting");
    return subscribe(
      source,
      (s) => {
        const old = latest.current;
        if (old?.run_id !== s.run_id) {
          setHistory([]);
          setRuntime(null);
          setFairness(null);
        }
        latest.current = s;
        setSnapshot(s);
        setHistory((h) => {
          const t = Date.now();
          return h.length && t - h[h.length - 1].at < 450
            ? h
            : [...h, historyPoint(s, t)].slice(-240);
        });
      },
      (value) => {
        setConnection(value);
        if (value === "stale" && latest.current)
          setHistory((h) =>
            h.length && h[h.length - 1].observed !== null
              ? [
                  ...h,
                  { ...historyPoint(latest.current!), observed: null },
                ].slice(-240)
              : h,
          );
      },
    );
  }, [source]);
  useEffect(() => {
    if (source !== "live" || !snapshot) return;
    const run = snapshot.run_id;
    let disposed = false;
    const abort = new AbortController();
    let pending = false;
    const load = async () => {
      if (pending) return;
      pending = true;
      const r = await Promise.allSettled([
        api<Runtime>("live", "runtime", undefined, { signal: abort.signal }),
        api<Fairness>("live", "fairness", undefined, { signal: abort.signal }),
      ]);
      if (!disposed) {
        const [a, b] = r;
        setRuntime(
          a.status === "fulfilled" && a.value.run_id === run ? a.value : null,
        );
        setFairness(
          b.status === "fulfilled" && b.value.run_id === run ? b.value : null,
        );
        setAuxError(
          r.some((v) => v.status === "rejected")
            ? "Process or fairness status is unavailable. No last-known status is treated as current."
            : "",
        );
      }
      pending = false;
    };
    void load();
    const timer = setInterval(load, 1500);
    return () => {
      disposed = true;
      abort.abort();
      clearInterval(timer);
    };
  }, [source, snapshot?.run_id]);
  const attempt = async (i: Intent) => {
    setBusy(true);
    setMessage("Waiting for the backend to confirm…");
    pendingIntent.current = i;
    setUnresolved(i);
    try {
      const op = await sendIntent(i, (o) => {
        if (alive.current) setOperation(o);
      });
      if (alive.current) {
        setMessage(op.message ?? "Applied");
        pendingIntent.current = null;
        setUnresolved(null);
      }
    } catch (e) {
      if (alive.current) {
        setMessage(
          e instanceof Error ? e.message : "Unable to confirm operation",
        );
        if (e instanceof ApiError && e.status >= 400 && e.status < 500) {
          pendingIntent.current = null;
          setUnresolved(null);
        }
      }
    } finally {
      if (alive.current) setBusy(false);
    }
  };
  const act = async (path: string, fields: Record<string, unknown>) => {
    if (
      busyRef.current ||
      pendingIntent.current ||
      !latest.current ||
      connection === "stale" ||
      connection === "connecting"
    )
      return;
    setBusy(true);
    try {
      const fresh = await state(source);
      if (fresh.run_id !== latest.current.run_id)
        throw new Error(
          "The run changed. Review the current state before trying again.",
        );
      if (alive.current) await attempt(intent(source, fresh, path, fields));
    } catch (e) {
      setMessage(
        e instanceof Error
          ? e.message
          : "Unable to read current control revision",
      );
      setBusy(false);
    }
  };
  return {
    source,
    setSource,
    snapshot,
    connection,
    history,
    runtime,
    fairness,
    auxError,
    busy,
    setBusy,
    message,
    setMessage,
    operation,
    unresolved,
    act,
    retry: () =>
      !busyRef.current &&
      pendingIntent.current &&
      attempt(pendingIntent.current),
  };
}
