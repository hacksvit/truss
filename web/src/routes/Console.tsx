import {useState} from 'react';
import {useSnapshot} from '../state';
import SiteCapacity from '../components/SiteCapacity';
import MemberCard from '../components/MemberCard';
import MemberDrawer from '../components/MemberDrawer';
import JudgeControls from '../components/JudgeControls';
import EventTimeline from '../components/EventTimeline';
import DebtTable from '../components/DebtTable';
import MetricsStrip from '../components/MetricsStrip';
const RUNNING=[
 {h:'1 message broker',p:'A real authenticated Mosquitto instance. Every process talks over it with its own credentials, and role ACLs stop the coordinator from even subscribing to private device topics.'},
 {h:'1 coordinator',p:'Collects offers, reserves every registered floor, then water-fills the surplus. It proposes; a separate ledger decides what may actually be issued.'},
 {h:'5 household agents',p:'One per home. Reads its own private device profile, publishes only an aggregate offer, and turns an accepted lease into per-device commands.'},
 {h:'5 independent enforcers',p:'Separate processes with their own clocks. They do not trust the agent that talks to them — when a deadline passes they drop to baseline on their own.'},
 {h:'Lease lifetime 6000 ms',p:'Timed from the moment the home asks, not from when the reply lands, so a delayed grant can never quietly extend anyone\u2019s permission.'},
 {h:'Recovery hold 6400 ms',p:'A restarted coordinator issues nothing until a full hold has passed, because it cannot know what it promised before it died.'}
];

function Runbook(){return <section className="runbook">
 <div className="section-label">WHAT IS ACTUALLY RUNNING BEHIND THIS SCREEN</div>
 <div className="runbook-grid">{RUNNING.map(r=><div className="runbook-item" key={r.h}><h4>{r.h}</h4><p>{r.p}</p></div>)}</div>
 <p className="runbook-note">Proposed, issued, reserved and observed are four different facts and this console never merges them. Reserved watts conservatively include grants that may still be outstanding, so during a cap drop the reserved band can legitimately sit above the new cap &mdash; permission already issued does not vanish because a number changed on screen. A missing reading shows as <code>UNKNOWN</code>, never as zero.</p>
</section>;}

export default function Console(){const {snapshot,connection}=useSnapshot();const [selected,setSelected]=useState<string|null>(null);const member=snapshot?.members.find(m=>m.id===selected);
 return <main className="console"><div className="page-heading"><div><div className="section-label">OPERATOR CONSOLE</div><h1>One limit. Five households.</h1></div><span className={`connection ${connection==='stale'?'hatched':''}`}>{connection}</span></div>{!snapshot?<section className="panel empty"><h2>Waiting for the mock server</h2><p>Start the backend with <code>truss mock</code>. No live data is assumed while disconnected.</p></section>:<><div className={connection==='stale'?'stale-data':''}><SiteCapacity site={snapshot.site}/><div className="section-label members-label">02 / HOUSEHOLDS · CLICK TO INSPECT</div><div className="member-grid">{snapshot.members.map(m=><MemberCard key={m.id} member={m} onSelect={()=>setSelected(m.id)}/>)}</div><MetricsStrip metrics={snapshot.metrics}/></div>{connection==='stale'&&<p role="alert">Connection is stale. All displayed values are last known; compliance is unverified.</p>}<JudgeControls snapshot={snapshot} disabled={connection==='stale'}/><div className="bottom-grid"><EventTimeline events={snapshot.events}/><DebtTable members={snapshot.members}/></div>{member&&<MemberDrawer member={member} onClose={()=>setSelected(null)}/>}</>}<Runbook/></main>;
}
