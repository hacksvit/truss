import {it,expect,afterEach} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import MetricsStrip from '../src/components/MetricsStrip';
import SiteCapacity from '../src/components/SiteCapacity';
import fixtures from '../../fixtures/snapshots.json';
import type {SiteView} from '../src/contracts';
afterEach(cleanup);
it('does not render unknown metrics as successful measurements',()=>{
 render(<MetricsStrip metrics={{cap_compliance_pct:null,time_to_safe_ms:null,lease_model_violations:null,ack_success_pct:null,unknown_samples:1}}/>);
 expect(screen.getAllByText('Not measured').length).toBe(2);
 expect(screen.getByText('No live oracle')).toBeTruthy();
 expect(screen.queryByText('100.0%')).toBeNull();
});
it('renders the unknown observation fixture without asserting zero draw',()=>{
 const site=fixtures.find(x=>x.case==='stale_member')!.data.site as SiteView;
 const {container}=render(<SiteCapacity site={site}/>);
 expect(container.textContent).toContain('Unknown');
});
