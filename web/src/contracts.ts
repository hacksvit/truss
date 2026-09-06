/** Operator contracts, owner M4. Full future wire specification: plans/20. */
export type Source = 'mock'|'live'|'replay';
export type Quality = 'fresh'|'stale'|'unknown';
export interface LeaseView {remaining_ms:number|null;sample_age_ms:number|null;quality:Quality;plant_confirmed:boolean;ref:unknown|null}
export interface DeviceView {id:string;kind:string;label:string;w:number|null;requested_w:number;state:string;quality:Quality;ack:string;protected:boolean;control_policy:'protected'|'flexible'|'unclassified';curtailment_eligible:boolean;decision:Record<string,unknown>|null}
export interface MemberView {id:string;floor_w:number;max_w:number;target_w:number|null;issued_w:number|null;reserved_w:number;observed_w:number|null;observed_quality:Quality;debt_wh:number;weight:number;lease:LeaseView;status:string;devices:DeviceView[];basis:Record<string,unknown>|null}
export interface SiteView {id:string;cap_w:number;baseline_sum_w:number;reserved_member_w:number;measurement_reserve_w:number;external_bound_w:number;unverified_member_reservation_w:number;exposure_w:number;observed_w:number|null;observed_quality:Quality;state:string;coordinator_status:string;recovering_ms_remaining:number|null;compliance:string;deficit_w:number;rule:string}
export interface EventView {seq:number;at:string;text:string;code:string}
export interface MetricsView {cap_compliance_pct:number|null;time_to_safe_ms:number|null;lease_model_violations:number|null;ack_success_pct:number|null;unknown_samples:number}
export interface Operation {operation_id:string;status:string;control_revision:number;message:string|null}
export interface Snapshot {schema:'truss.ui_snapshot.v1';run_id:string;stream_id:string;revision:number;control_revision:number;source:Source;site:SiteView;members:MemberView[];events:EventView[];metrics:MetricsView;operations:Operation[];capabilities:{chaos:boolean;protect:boolean;replay:boolean;lab:boolean}}
export interface BenchmarkResult {members:number;seed:number;samples_ms:number[];complete:boolean;median_ms:number|null;p95_ms:number|null;python:string;os:string;scope:string;warmups:number}
export function isSnapshot(value:unknown):value is Snapshot {
  if (!value || typeof value !== 'object') return false;
  const v=value as Partial<Snapshot>;
  return v.schema==='truss.ui_snapshot.v1' && typeof v.stream_id==='string' && typeof v.run_id==='string' && Number.isSafeInteger(v.revision) && ['live','mock','replay'].includes(v.source??'') && Array.isArray(v.members) && Array.isArray(v.events) && !!v.site && !!v.metrics && !!v.capabilities;
}
