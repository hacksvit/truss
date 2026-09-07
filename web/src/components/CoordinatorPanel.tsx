import {DEVICES,assign} from './houseKit';

const FLOOR=[160,170,180];
const NAMES=['A','B','C'];
const RESERVE=100;

/** The coordinator opened up: what it is handed, the rule it applies, what it
 *  refuses to do, and what it sends back — computed live from the same numbers
 *  the scene is running on, not illustrated. */
export default function CoordinatorPanel({cap,useful,budgets,onClose}:{
 cap:number; useful:number[]; budgets:number[]; onClose:()=>void;
}){
 const floors=FLOOR.reduce((a,b)=>a+b,0);
 const spare=cap-RESERVE-floors;
 const feasible=spare>=0;
 const issued=budgets.reduce((a,b)=>a+b,0);
 const surplus=budgets.map((b,i)=>b-FLOOR[i]);
 const level=Math.max(...surplus);

 return <div className="coord-panel" role="dialog" aria-label="Coordinator internals">
  <div className="coord-head">
   <div>
    <span className="coord-eyebrow">COORDINATOR · INTERNALS</span>
    <h2>How the split is decided</h2>
   </div>
   <button className="coord-close" onClick={onClose} aria-label="Close">E</button>
  </div>

  <div className="coord-grid">

   <section className="coord-step">
    <span className="coord-n">01</span>
    <h3>What comes in</h3>
    <p>Each home publishes two numbers. No appliance list ever leaves the house —
    the broker forbids this process from even subscribing to those topics.</p>
    <table>
     <thead><tr><th>home</th><th>floor</th><th>useful</th></tr></thead>
     <tbody>{NAMES.map((n,i)=>
      <tr key={n}><td>{n}</td><td>{FLOOR[i]} W</td><td>{useful[i]} W</td></tr>)}
     </tbody>
    </table>
   </section>

   <section className="coord-step">
    <span className="coord-n">02</span>
    <h3>Reserve the floors first</h3>
    <p>Protected baselines come off the top before anything is shared. What is
    left is the only thing in play.</p>
    <dl className="coord-sum">
     <div><dt>supply</dt><dd>{cap} W</dd></div>
     <div><dt>− measurement reserve</dt><dd>{RESERVE} W</dd></div>
     <div><dt>− protected floors</dt><dd>{floors} W</dd></div>
     <div className={feasible?'coord-ok':'coord-bad'}>
      <dt>= surplus to share</dt><dd>{spare} W</dd></div>
    </dl>
   </section>

   <section className="coord-step">
    <span className="coord-n">03</span>
    <h3>Water-fill the surplus</h3>
    <p>Raise every home's level together. A home that tops out stops taking and
    the rest keep rising — so small askers get everything, big askers split the
    rest equally. <em>O(n log n)</em>, deterministic, no optimiser.</p>
    {feasible&&<div className="coord-bars">
     {NAMES.map((n,i)=>{
      const head=Math.max(0,useful[i]-FLOOR[i]);
      const got=surplus[i];
      return <div className="coord-bar" key={n}>
       <span>{n}</span>
       <div className="coord-track">
        <i className="coord-floor" style={{width:'22%'}}/>
        <i className="coord-got" style={{width:(78*got/Math.max(1,head))+'%'}}/>
       </div>
       <b>{got} W</b>
      </div>;
     })}
     <p className="coord-note">common level ≈ {level} W above floor</p>
    </div>}
   </section>

   <section className="coord-step">
    <span className="coord-n">04</span>
    <h3>The gate that can say no</h3>
    <p>The planner only <em>proposes</em>. A separate reservation ledger decides
    what may issue, and it counts a grant it could not deliver against the cap
    for its full life. An independent validator that does not import the
    allocator re-checks every plan and can veto it.</p>
    <dl className="coord-sum">
     <div><dt>issued</dt><dd>{issued} W</dd></div>
     <div><dt>headroom left</dt><dd>{cap-RESERVE-issued} W</dd></div>
     <div><dt>lease lifetime</dt><dd>6000 ms</dd></div>
     <div><dt>recovery hold</dt><dd>6400 ms</dd></div>
    </dl>
   </section>

   <section className="coord-step">
    <span className="coord-n">05</span>
    <h3>What goes back out</h3>
    <p>Not a command — a lease. “This many watts, until this moment.” The clock
    starts when the home <em>asks</em>, so a slow reply can never quietly extend
    it. Nothing is ever sent to switch a load off; permission simply expires.</p>
    <table>
     <thead><tr><th>home</th><th>granted</th><th>then</th></tr></thead>
     <tbody>{NAMES.map((n,i)=>{
      const a=assign(budgets[i]);
      const on=DEVICES.filter(d=>a[d.id]>0).length;
      return <tr key={n}>
       <td>{n}</td><td>{budgets[i]} W</td>
       <td className="muted">{on}/4 devices · floor {FLOOR[i]} W</td>
      </tr>;
     })}</tbody>
    </table>
   </section>

   <section className="coord-step coord-danger">
    <span className="coord-n">06</span>
    <h3>When it cannot be done</h3>
    <p>If the supply is below the protected floors plus reserve, there is no
    split that keeps every promise. It reports <strong>INFEASIBLE</strong> and
    names the shortfall rather than quietly breaching a floor.</p>
    {!feasible
     ? <p className="coord-bad">Currently infeasible — short by {-spare} W.</p>
     : <p className="muted">Currently feasible with {spare} W of surplus.</p>}
   </section>

  </div>

  <p className="coord-foot">Kill this process and nothing is sent. Every lease
  runs out and each home falls to its own floor. Safety is a property of the
  protocol, not of this planner.</p>
 </div>;
}
