import {SnapshotProvider} from './state';
import Showcase from './routes/Showcase';
import Console from './routes/Console';
import Lab from './routes/Lab';
import BoundaryBanner from './components/BoundaryBanner';
export default function App(){
 const route=location.pathname;
 return <><header className="site-header"><a className="wordmark" href="/">TRUSS</a><nav aria-label="Main navigation"><a href="/" aria-current={route==='/'?'page':undefined}>Overview</a><a href="/console" aria-current={route==='/console'?'page':undefined}>Console</a><a href="/lab" aria-current={route==='/lab'?'page':undefined}>Lab</a></nav><span className="header-note">LOCAL CAPACITY COORDINATION</span></header><BoundaryBanner/>{route==='/console'?<SnapshotProvider><Console/></SnapshotProvider>:route==='/lab'?<Lab/>:<Showcase/>}<footer>Virtual appliances only · No mains switching · No certification · No savings claims</footer></>;
}
