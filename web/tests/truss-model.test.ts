import {describe,it,expect} from 'vitest';
import {readFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {MEMBERS,SITE_MEMBERS,RESERVE_W,LEASE_TTL_MS,RECOVERY_HOLD_MS,
        allocate,assign,unusable,usefulFor,exposure,admits,Frac,WANTS} from '../src/components/trussModel';

// vitest runs with the web/ directory as its root, so the repo config sits one
// level up; fall back to the repo root in case it is invoked from there
const readJson=(p:string)=>{
 const here=resolve(process.cwd(),'..',p);
 return JSON.parse(readFileSync(existsSync(here)?here:resolve(process.cwd(),p),'utf8'));
};

/** The scene is only worth showing if its numbers are the backend's numbers.
 *  These read the real config and compare against output captured from the
 *  Python allocator/local policy, so drift in either direction fails here. */
describe('the TS port matches config/',()=>{
 it('carries every registered envelope from config/member-*.json',()=>{
  for(const m of MEMBERS){
   const raw=readJson(`config/${m.id}.json`);
   expect(raw.member_id).toBe(m.id);
   expect(m.devices.map(d=>d.id)).toEqual(raw.devices.map((d:{device_id:string})=>d.device_id));
   for(const d of m.devices){
    const r=raw.devices.find((x:{device_id:string})=>x.device_id===d.id);
    expect([d.id,d.baseline,d.max,d.policy,d.priority,d.actuation])
     .toEqual([r.device_id,r.baseline_w,r.max_w,r.control_policy,r.priority,
               r.actuation??'continuous']);
   }
   // floor is the sum of protected baselines; max is floor plus every step
   expect(m.floor).toBe(m.devices.reduce((a,d)=>a+d.baseline,0));
   expect(m.max).toBe(m.devices.reduce((a,d)=>a+d.max,0));
  }
 });

 it('matches the floors, maxima and site reserve in config/run.json',()=>{
  const run=readJson('config/run.json');
  expect(RESERVE_W).toBe(run.measurement_reserve_w);
  expect(MEMBERS.length).toBe(run.members.length);
  for(const entry of run.members){
   const m=MEMBERS.find(x=>x.id===entry.member_id)!;
   expect(m).toBeDefined();
   expect([m.floor,m.max]).toEqual([entry.floor_w,entry.max_w]);
  }
 });

 it('pins the lease and recovery constants the schemas enforce',()=>{
  expect(LEASE_TTL_MS).toBe(6000);
  expect(RECOVERY_HOLD_MS).toBe(6400);
 });
});

const offers=()=>SITE_MEMBERS.map(m=>
 ({id:m.id,floor:m.floor,useful:usefulFor(m,WANTS[m.id])}));

describe('allocate() reproduces the Python allocator',()=>{
 // captured from `truss.allocator.allocate` on the same offers and reserve
 it.each([
  [1800,{'member-a':665,'member-b':350,'member-c':685},0],
  [3200,{'member-a':990,'member-b':350,'member-c':910},0],
  [900, {'member-a':256,'member-b':266,'member-c':276},2]
 ])('cap %i W splits as the backend does',(cap,budgets,remainder)=>{
  const p=allocate(offers(),cap as number,RESERVE_W);
  expect(p.feasible).toBe(true);
  expect(p.budgets).toEqual(budgets);
  expect(p.remainder.toNumber()).toBe(remainder);
 });

 it('reports the shortfall instead of breaching a floor',()=>{
  const p=allocate(offers(),560,RESERVE_W);
  expect(p.feasible).toBe(false);
  expect(p.deficit).toBe(50);
  expect(p.budgets).toEqual({});
 });

 it('never grants a home more than it asked for',()=>{
  const o=offers();
  const p=allocate(o,5000,RESERVE_W);
  for(const x of o) expect(p.budgets[x.id]).toBeLessThanOrEqual(x.useful);
 });

 it('never issues more than the usable supply',()=>{
  for(const cap of [700,1200,1800,2400,3200]){
   const p=allocate(offers(),cap,RESERVE_W);
   if(!p.feasible) continue;
   const issued=Object.values(p.budgets).reduce((a,b)=>a+b,0);
   expect(issued+RESERVE_W).toBeLessThanOrEqual(cap);
  }
 });
});

describe('assign() reproduces the Python local policy',()=>{
 // captured from `truss.local_policy.assign` over the whole device list
 it.each([
  ['member-a',665,{'protected-load':120,router:40,charger:180,heater:0},325],
  ['member-b',665,{'protected-load':130,router:40,charger:180,heater:315},0],
  ['member-c',350,{'protected-load':140,router:40,charger:170,heater:0},0],
  ['member-b',900,{'protected-load':130,router:40,charger:180,heater:550},0]
 ])('%s at %i W',(id,budget,expected,stranded)=>{
  const m=MEMBERS.find(x=>x.id===id)!;
  expect(assign(m,budget as number)).toEqual(expected);
  expect(unusable(m,budget as number)).toBe(stranded);
 });

 it('strands watts only behind a binary load',()=>{
  // member-a's heater is the one binary device in the whole config
  const a=MEMBERS[0], b=MEMBERS[1];
  expect(unusable(a,665)).toBeGreaterThan(0);
  expect(unusable(b,665)).toBe(0);
 });

 it('refuses a budget that cannot preserve the registered baselines',()=>{
  expect(()=>assign(MEMBERS[0],100)).toThrow();
 });

 it('leaves a device the home is not asking for at its baseline',()=>{
  const b=MEMBERS[1];
  const got=assign(b,900,WANTS['member-b']);
  expect(got.heater).toBe(0);
  expect(got.charger).toBe(180);
 });

 it('useful equals the registered maximum when everything is wanted',()=>{
  for(const m of MEMBERS)
   expect(usefulFor(m,new Set(m.devices.map(d=>d.id)))).toBe(m.max);
 });
});

describe('the reservation gate',()=>{
 it('assumes every member is at its maximum during the recovery hold',()=>{
  const e=exposure(SITE_MEMBERS,{},true);
  expect(e).toEqual({'member-a':990,'member-b':1040,'member-c':1090});
 });

 it('holds a grant against the cap for its whole life, not just while drawn',()=>{
  const held={'member-a':900};
  expect(exposure(SITE_MEMBERS,held,false)['member-a']).toBe(900);
 });

 it('refuses a grant that would put outstanding authority over the cap',()=>{
  const held={'member-a':900,'member-b':900};
  expect(admits(SITE_MEMBERS,held,'member-c',900,1800,RESERVE_W).ok).toBe(false);
  expect(admits(SITE_MEMBERS,held,'member-c',180,3200,RESERVE_W).ok).toBe(true);
 });
});

describe('Frac stays exact',()=>{
 it('does not drift where a float would',()=>{
  let t=new Frac(0);
  for(let i=0;i<10;i++) t=t.add(new Frac(1,3));
  expect([t.n,t.d]).toEqual([10,3]);
  expect(t.floor()).toBe(3);
 });
 it('floors toward zero the way integer division does',()=>{
  expect(new Frac(1700,3).floor()).toBe(566);
 });
});
