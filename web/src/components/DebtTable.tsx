import type {MemberView} from '../contracts';
import {energy} from '../format';
export default function DebtTable({members}:{members:MemberView[]}){return <section className="panel debt"><div className="section-label">SERVICE DEFICIT</div><div className="debt-values">{members.map(m=><div key={m.id}><small>{m.id}</small><strong>{energy(m.debt_wh)}</strong></div>)}</div><p className="muted">Equal-surplus mode. Deficit weighting is disabled; these values are not measured energy savings.</p></section>;}
