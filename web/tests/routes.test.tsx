import {it,expect,afterEach,vi} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import Showcase from '../src/routes/Showcase';
import Lab from '../src/routes/Lab';
import BoundaryBanner from '../src/components/BoundaryBanner';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('keeps a mock boundary label available',()=>{
 // the banner is no longer mounted in App by request; the component still exists
 // so the labelled-mock affordance can be put back without rebuilding it
 const {container}=render(<BoundaryBanner/>);
 expect(container.textContent).toContain('MOCK');
});
it('renders the homepage reel with every topic',()=>{
 vi.stubGlobal('matchMedia',()=>({matches:false,addEventListener:()=>{},removeEventListener:()=>{}}));
 const {container}=render(<Showcase/>);
 // A finite story exposes eight unique cards.
 const cards=container.querySelectorAll('.story-card');
 expect(cards.length).toBe(8);
 expect([...cards].filter(c=>c.getAttribute('aria-hidden')!=='true').length).toBe(8);
 expect(container.textContent).toContain('Try Truss');
 expect(container.textContent).toContain('Missing readings stay unknown');
});
it('renders lab controls without a backend',()=>{
 const {container}=render(<Lab/>);
 expect(screen.getByRole('button',{name:/Run measured batch/i})).toBeTruthy();
 expect(container.textContent).toContain('allocator');
});
