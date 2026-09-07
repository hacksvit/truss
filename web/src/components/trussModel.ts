/** A faithful TypeScript port of the protocol cores the live runtime actually
 *  runs, so the 3D site shows the numbers the backend would produce rather than
 *  a plausible-looking approximation.
 *
 *  Mirrors, function for function:
 *    src/truss/allocator.py      allocate()
 *    src/truss/local_policy.py   assign(), unusable_w()
 *    src/truss/reservations.py   ReservationLedger.exposure()
 *    src/truss/transport.py      topic_for()
 *    config/run.json, config/member-*.json   the registered envelopes
 *
 *  web/tests/truss-model.test.ts reads those JSON files directly and fails if
 *  this file drifts away from them.
 */

// ---------------------------------------------------------------- rationals

function gcd(a:number,b:number):number{ while(b){ const t=a%b; a=b; b=t; } return a<0?-a:a; }

/** The backend allocator works in exact `Fraction`s so that the water level is
 *  not a float guess. Two implementations only agree to the watt if this one
 *  does the same. */
export class Frac{
 readonly n:number; readonly d:number;
 constructor(n:number,d=1){
  if(d===0) throw new Error('zero denominator');
  if(d<0){ n=-n; d=-d; }
  const g=gcd(Math.abs(n),d)||1;
  this.n=n/g; this.d=d/g;
 }
 add(o:Frac){ return new Frac(this.n*o.d+o.n*this.d,this.d*o.d); }
 sub(o:Frac){ return new Frac(this.n*o.d-o.n*this.d,this.d*o.d); }
 mul(o:Frac){ return new Frac(this.n*o.n,this.d*o.d); }
 div(o:Frac){ return new Frac(this.n*o.d,this.d*o.n); }
 /** <0, 0 or >0 — denominators are kept positive so cross-multiplying is safe */
 cmp(o:Frac){ return this.n*o.d-o.n*this.d; }
 floor(){ return Math.floor(this.n/this.d); }
 toNumber(){ return this.n/this.d; }
}
const F=(n:number,d=1)=>new Frac(n,d);

// ------------------------------------------------------------------ profiles

export type Policy='protected'|'flexible';
export type Actuation='continuous'|'binary';

export interface DeviceSpec{
 id:string; label:string;
 baseline:number; max:number;
 policy:Policy; priority:number;
 actuation:Actuation;
}

export interface MemberProfile{
 id:string;      // member-a
 name:string;    // A
 floor:number;   // registered minimum, = sum of protected baselines
 max:number;     // registered maximum, = floor + every flexible step
 devices:DeviceSpec[];
}

const dev=(id:string,label:string,baseline:number,max:number,policy:Policy,
           priority:number,actuation:Actuation='continuous'):DeviceSpec=>
 ({id,label,baseline,max,policy,priority,actuation});

/** Transcribed from config/member-{a..e}.json and config/run.json. Only the
 *  heater in member-a is a binary load — that asymmetry is in the real config
 *  and it is why one home strands watts it was allowed to draw. */
export const MEMBERS:MemberProfile[]=[
 {id:'member-a',name:'A',floor:160,max:990,devices:[
  dev('protected-load','Protected load',120,120,'protected',100),
  dev('router','Router and fixed lighting',40,40,'protected',90),
  dev('charger','Flexible charger',0,180,'flexible',60),
  dev('heater','Flexible heater',0,650,'flexible',20,'binary')]},
 {id:'member-b',name:'B',floor:170,max:1040,devices:[
  dev('protected-load','Protected load',130,130,'protected',100),
  dev('router','Router and fixed lighting',40,40,'protected',90),
  dev('charger','Flexible charger',0,180,'flexible',60),
  dev('heater','Flexible heater',0,690,'flexible',20)]},
 {id:'member-c',name:'C',floor:180,max:1090,devices:[
  dev('protected-load','Protected load',140,140,'protected',100),
  dev('router','Router and fixed lighting',40,40,'protected',90),
  dev('charger','Flexible charger',0,180,'flexible',60),
  dev('heater','Flexible heater',0,730,'flexible',20)]},
 {id:'member-d',name:'D',floor:190,max:1140,devices:[
  dev('protected-load','Protected load',150,150,'protected',100),
  dev('router','Router and fixed lighting',40,40,'protected',90),
  dev('charger','Flexible charger',0,180,'flexible',60),
  dev('heater','Flexible heater',0,770,'flexible',20)]},
 {id:'member-e',name:'E',floor:200,max:1190,devices:[
  dev('protected-load','Protected load',160,160,'protected',100),
  dev('router','Router and fixed lighting',40,40,'protected',90),
  dev('charger','Flexible charger',0,180,'flexible',60),
  dev('heater','Flexible heater',0,810,'flexible',20)]}
];

/** The three homes the 3D site draws. The console runs all five. */
export const SITE_MEMBERS=MEMBERS.slice(0,3);

/** Which flexible loads each home is currently asking to run. This is the only
 *  thing the scene invents — a real member derives it from what its appliances
 *  actually want right now — and it is what makes the three homes ask for
 *  different amounts instead of all publishing their registered maximum. */
export const WANTS:Record<string,Set<string>>={
 'member-a':new Set(['charger','heater']),   // wants everything: useful 990 W
 'member-b':new Set(['charger']),            // charger only:     useful 350 W
 'member-c':new Set(['heater']),             // heater only:      useful 910 W
 'member-d':new Set(['charger','heater']),
 'member-e':new Set(['charger'])
};

export const SITE_ID='hostel-demo';
export const RESERVE_W=100;      // config/run.json measurement_reserve_w
export const LEASE_TTL_MS=6000;  // schemas.py pins this to exactly 6000
export const RECOVERY_HOLD_MS=6400;

// ----------------------------------------------------------------- allocator

export interface Demand{ id:string; floor:number; useful:number; weight?:Frac }

export interface Proposal{
 feasible:boolean;
 budgets:Record<string,number>;
 continuous:Record<string,Frac>;
 /** watts by which the registered floors overrun the usable supply */
 deficit:number;
 /** watts lost to rounding each grant down to a whole watt */
 remainder:Frac;
 /** the common water level above the floors, for explaining the split */
 level:Frac;
}

/** Weighted max-min fair filling of the surplus above the registered floors.
 *  Straight port of allocator.py: raise every home's level together, and when
 *  a home tops out at its useful demand it stops taking so the rest keep
 *  rising. O(n log n), deterministic, no optimiser. */
export function allocate(offers:Demand[],cap:number,reserve=0):Proposal{
 const floors=offers.reduce((a,o)=>a+o.floor,0);
 const available=cap-reserve-floors;
 if(available<0)
  return {feasible:false,budgets:{},continuous:{},deficit:-available,
          remainder:F(0),level:F(0)};

 const active=offers
  .filter(o=>o.useful>o.floor)
  .map(o=>({t:F(o.useful-o.floor).div(o.weight??F(1)),id:o.id,w:o.weight??F(1)}))
  .sort((a,b)=>a.t.cmp(b.t)||(a.id<b.id?-1:a.id>b.id?1:0));

 let pool=F(available), level=F(0);
 let total=active.reduce((a,x)=>a.add(x.w),F(0));
 for(const {t,w} of active){
  if(total.n===0) break;
  const cost=t.sub(level).mul(total);
  if(cost.cmp(pool)>0){ level=level.add(pool.div(total)); pool=F(0); break; }
  pool=pool.sub(cost); level=t; total=total.sub(w);
 }

 const continuous:Record<string,Frac>={};
 for(const o of [...offers].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0)){
  const head=F(o.useful-o.floor);
  const share=(o.weight??F(1)).mul(level);
  continuous[o.id]=F(o.floor).add(head.cmp(share)<=0?head:share);
 }
 const budgets:Record<string,number>={};
 let sumC=F(0), sumB=0;
 for(const k of Object.keys(continuous)){
  budgets[k]=continuous[k].floor();
  sumC=sumC.add(continuous[k]); sumB+=budgets[k];
 }
 return {feasible:true,budgets,continuous,deficit:0,
         remainder:sumC.sub(F(sumB)),level};
}

// -------------------------------------------------------------- local policy

/** Household-local assignment. Only flexible output can yield, and a device the
 *  home is not currently asking for stays at its baseline — that is what makes
 *  its published `useful` smaller than its registered maximum.
 *  Port of local_policy.assign(). */
export function assign(profile:MemberProfile,budget:number,wanted?:Set<string>)
 :Record<string,number>{
 const baseline=profile.devices.reduce((a,d)=>a+d.baseline,0);
 if(budget<baseline) throw new Error('budget cannot preserve registered device baselines');
 const result:Record<string,number>={};
 for(const d of profile.devices) result[d.id]=d.baseline;
 let remaining=budget-baseline;
 const order=[...profile.devices].sort((a,b)=>
  (b.priority-a.priority)||(a.id<b.id?-1:a.id>b.id?1:0));
 for(const d of order){
  if(d.policy!=='flexible') continue;
  if(wanted&&!wanted.has(d.id)) continue;
  const step=d.max-d.baseline;
  // A binary load is a button, not a dial: it runs at its maximum or not at
  // all, so an unaffordable one is skipped and a lower-priority device may
  // still fit.
  const extra=d.actuation==='binary'?(step<=remaining?step:0):Math.min(remaining,step);
  result[d.id]+=extra; remaining-=extra;
 }
 return result;
}

/** Watts the household is allowed to draw but cannot reach, because a binary
 *  load's whole step does not fit in what is left. Port of unusable_w(). */
export function unusable(profile:MemberProfile,budget:number,wanted?:Set<string>){
 const a=assign(profile,budget,wanted);
 return budget-Object.values(a).reduce((x,y)=>x+y,0);
}

/** What the home publishes as `useful_w`: its floor plus every flexible step it
 *  currently wants. Equals the registered maximum when it wants everything. */
export function usefulFor(profile:MemberProfile,wanted:Set<string>){
 return profile.devices.reduce((a,d)=>
  a+d.baseline+(d.policy==='flexible'&&wanted.has(d.id)?d.max-d.baseline:0),0);
}

// ---------------------------------------------------------------- the gate

/** ReservationLedger.exposure(): what the gate believes could be drawn right
 *  now — possible authority, not last measured draw. During the recovery hold
 *  after a restart it assumes every member is at its registered maximum, which
 *  is why no new grant is admitted until the hold ends. */
export function exposure(members:MemberProfile[],held:Record<string,number>,
                         recovering:boolean):Record<string,number>{
 const out:Record<string,number>={};
 for(const m of members) out[m.id]=recovering?m.max:Math.max(m.floor,held[m.id]??0);
 return out;
}

/** The admission test from ReservationLedger.admit(): a grant is only issued if
 *  every outstanding reservation plus this one still fits under the cap. */
export function admits(members:MemberProfile[],held:Record<string,number>,
                       memberId:string,amount:number,cap:number,reserve:number){
 const current=exposure(members,held,false);
 current[memberId]=Math.max(current[memberId],amount);
 const total=Object.values(current).reduce((a,b)=>a+b,0);
 return {ok:total+reserve<=cap,total};
}

// ------------------------------------------------------------------- topics

/** Port of transport.topic_for(). The two marked private are the ones
 *  transport.validate_delivery() refuses to hand to the coordinator role. */
export function topicsFor(memberId:string){
 const root=`truss/v1/site/${SITE_ID}/member/${memberId}`;
 return [
  {leaf:'offer',      topic:`${root}/offer`,         dir:'up'  as const, private:false},
  {leaf:'lease',      topic:`${root}/lease`,         dir:'down'as const, private:false},
  {leaf:'lease/ack',  topic:`${root}/lease/ack`,     dir:'up'  as const, private:false},
  {leaf:'meter',      topic:`${root}/meter`,         dir:'up'  as const, private:false},
  {leaf:'device/…',   topic:`${root}/device/+/command`,dir:'up'as const, private:true},
  {leaf:'plant',      topic:`${root}/plant/status`,  dir:'up'  as const, private:true}
 ];
}
export const PLAN_TOPIC=`truss/v1/site/${SITE_ID}/plan`;
export const CAPACITY_TOPIC=`truss/v1/site/${SITE_ID}/event/capacity`;
export const COORD_STATUS_TOPIC=`truss/v1/site/${SITE_ID}/coordinator/status`;
