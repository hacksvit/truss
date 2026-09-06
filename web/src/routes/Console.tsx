import {useState} from 'react';
import {useSnapshot} from '../state';
import SiteCapacity from '../components/SiteCapacity';
import MemberCard from '../components/MemberCard';
import MemberDrawer from '../components/MemberDrawer';
import JudgeControls from '../components/JudgeControls';
import EventTimeline from '../components/EventTimeline';
import DebtTable from '../components/DebtTable';
import MetricsStrip from '../components/MetricsStrip';
export default function Console(){const {snapshot,connection}=useSnapshot();const [selected,setSelected]=useState<string|null>(null);const member=snapshot?.members.find(m=>m.id===selected);
 return <main className="console"><div className="page-heading"><div><div className="section-label">OPERATOR CONSOLE</div><h1>One limit. Five households.</h1></div><span className={`connection ${connection==='stale'?'hatched':''}`}>{connection}</span></div>{!snapshot?<section className="panel empty"><h2>Waiting for the mock server</h2><p>Start the backend with <code>truss mock</code>. No live data is assumed while disconnected.</p></section>:<><div className={connection==='stale'?'stale-data':''}><SiteCapacity site={snapshot.site}/><div className="section-label members-label">02 / HOUSEHOLDS · CLICK TO INSPECT</div><div className="member-grid">{snapshot.members.map(m=><MemberCard key={m.id} member={m} onSelect={()=>setSelected(m.id)}/>)}</div><MetricsStrip metrics={snapshot.metrics}/></div>{connection==='stale'&&<p role="alert">Connection is stale. All displayed values are last known; compliance is unverified.</p>}<JudgeControls snapshot={snapshot} disabled={connection==='stale'}/><div className="bottom-grid"><EventTimeline events={snapshot.events}/><DebtTable members={snapshot.members}/></div>{member&&<MemberDrawer member={member} onClose={()=>setSelected(null)}/>}</>}</main>;
}
