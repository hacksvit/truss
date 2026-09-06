import {describe,it,expect} from 'vitest';
import {acceptRevision} from '../src/stream';
import {isSnapshot,type Snapshot} from '../src/contracts';
import fixtures from '../../fixtures/snapshots.json';
const s=fixtures[0].data as unknown as Snapshot;
describe('snapshot ordering',()=>{
 it('rejects duplicate and older revisions',()=>{
  expect(acceptRevision(s,s,'mock')).toBe(false);
  expect(acceptRevision(s,{...s,revision:s.revision-1},'mock')).toBe(false);
  expect(acceptRevision(s,{...s,revision:s.revision+1},'mock')).toBe(true);
 });
 it('never accepts another source',()=>expect(acceptRevision(null,s,'live')).toBe(false));
 it('permits an explicitly new stream',()=>expect(acceptRevision(s,{...s,stream_id:'new',revision:0},'mock')).toBe(true));
 it('validates the checked fixture and rejects empty data',()=>{expect(isSnapshot(s)).toBe(true);expect(isSnapshot({})).toBe(false);});
});
