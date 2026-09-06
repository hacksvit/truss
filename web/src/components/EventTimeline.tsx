import type {EventView} from '../contracts';
export default function EventTimeline({events}:{events:EventView[]}){return <section className="panel timeline"><div className="section-label">04 / EVENT TRAIL</div>{[...events].reverse().slice(0,6).map(e=><div className="event" key={e.seq}><time>{new Date(e.at).toLocaleTimeString()}</time><p>{e.text}</p></div>)}</section>;}
