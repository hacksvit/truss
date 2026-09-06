import type {Snapshot,Operation,BenchmarkResult,Source} from './contracts';
export async function request<T>(path:string,body?:unknown,key?:string):Promise<T> {
 const response=await fetch(`/api/v1/${path}`,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(key?{'Idempotency-Key':key}:{})},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(path.startsWith('lab/')?15000:3000)});
 const value=await response.json();
 if(!response.ok) throw new Error(value.error?.message??`Request failed (${response.status})`);
 return value as T;
}
export const getState=(source:Source)=>request<Snapshot>(`state?source=${source}`);
export const submitControl=(path:string,s:Snapshot,fields:Record<string,unknown>,key:string)=>request<Operation>(path,{run_id:s.run_id,source:s.source,expected_control_revision:s.control_revision,...fields},key);
export const getOperation=(id:string)=>request<Operation>(`operations/${id}`);
export const runBenchmark=(members:number)=>request<BenchmarkResult>('lab/benchmark',{members,seed:42});
