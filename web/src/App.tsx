import {SnapshotProvider} from './state';
import Showcase from './routes/Showcase';
import Console from './routes/Console';
import Lab from './routes/Lab';
import BoundaryBanner from './components/BoundaryBanner';
import Chrome from './components/Chrome';

function Stub({title}:{title:string}){return <main className="empty"><h2>{title}</h2><p>Not built yet. The shell, navigation and theming are in place; this page's content is the next piece of work.</p><p className="muted"><a href="/console">Console</a> · <a href="/lab">Lab</a></p></main>;}

export default function App(){
 const route=location.pathname;
 const page=route==='/console'?<SnapshotProvider><Console/></SnapshotProvider>
  :route==='/lab'?<Lab/>
  :route==='/info'?<Stub title="Info"/>
  :route==='/example'?<Stub title="Example"/>
  :route==='/credits'?<Stub title="Credits"/>
  :<Showcase/>;
 return <><Chrome route={route}/><div className="chrome-spacer"/><BoundaryBanner/>{page}<footer>Virtual appliances only · No mains switching · No certification · No savings claims</footer></>;
}
