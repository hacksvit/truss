import type {
  Snapshot,
  MemberView,
  SiteView,
  EventView,
  Operation,
} from "../contracts";
export type ConsoleSource = "live" | "mock";
export type Rule = "equal_surplus" | "debt_weighted_surplus";
export type ConsoleMember = MemberView & {
  useful_w?: number;
  firm_w?: number;
  unusable_w?: number;
  sample_age_ms?: number | null;
};
export type ConsoleSnapshot = Omit<
  Snapshot,
  "members" | "site" | "operations" | "events"
> & {
  generated_at: string;
  event_cursor: number;
  members: ConsoleMember[];
  site: SiteView & {
    cap_revision: number;
    available_for_new_grants_w: number;
    unusable_w?: number;
    oldest_sample_age_ms?: number | null;
    timing?: Record<string, number | null>;
  };
  capabilities: Snapshot["capabilities"] & { debt_weighting?: boolean };
  operations: ConsoleOperation[];
  events: (EventView & { kind?: string; member_id?: string | null })[];
};
export type ConsoleOperation = Operation & {
  run_id: string;
  kind: string;
  error?: string | null;
  created_at?: string;
  finished_at?: string | null;
};
export interface Runtime {
  run_id: string;
  processes: {
    name: string;
    pid: number;
    running: boolean;
    exit_code: number | null;
  }[];
  evidence_error: string | null;
  recording_full: boolean;
}
export interface Fairness {
  run_id: string;
  desired_rule: Rule;
  effective_rule: Rule;
  available: boolean;
  error: string | null;
  scale_wh: number;
  maximum_wh: number;
  frozen_gap_ms: number;
  members: { member_id: string; debt_wh: number; weight: number }[];
}
export interface HistoryPoint {
  at: number;
  label: string;
  cap: number;
  exposure: number;
  observed: number | null;
  proposed: number | null;
  issued: number | null;
}
export interface Sample {
  elapsed_ms: number;
  snapshot: ConsoleSnapshot;
}
export interface Check {
  label: string;
  status: "observed" | "not_observed" | "inconclusive";
  detail: string;
}
export interface DrillReport {
  schema: "truss.console_drill.v1";
  id: string;
  kind: DrillKind;
  run_id: string;
  source: "live";
  initial_snapshot: ConsoleSnapshot;
  started_at: string;
  finished_at: string | null;
  phase: string;
  status: "running" | "observed" | "inconclusive" | "failed";
  checks: Check[];
  operations: ConsoleOperation[];
  samples: Sample[];
  missing_samples: number;
  events: ConsoleSnapshot["events"];
  recovery: string;
  error?: string;
  scope: string;
}
export type DrillKind =
  | "coordinator"
  | "delayed_grant"
  | "partition"
  | "double_restart"
  | "infeasible";
export interface Recording {
  recorded_run_id: string;
  bytes: number;
  replayable: boolean;
}
export interface Replay {
  replay_id: string;
  recorded_run_id: string;
  sha256: string;
  gap: boolean;
  frame_seq: number;
  first_seq: number;
  last_seq: number;
  frame_count: number;
  playing: boolean;
  position_ms: number;
  duration_ms: number;
  snapshot: ConsoleSnapshot;
}
