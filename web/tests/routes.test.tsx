import {it,expect,afterEach} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import Showcase from '../src/routes/Showcase';
import Lab from '../src/routes/Lab';
import BoundaryBanner from '../src/components/BoundaryBanner';
afterEach(cleanup);
it('keeps a mock boundary label available',()=>{
 // the banner is no longer mounted in App by request; the component still exists
 // so the labelled-mock affordance can be put back without rebuilding it
 const {container}=render(<BoundaryBanner/>);
 expect(container.textContent).toContain('MOCK');
});
it('renders the homepage reel with every topic',()=>{
 const {container}=render(<Showcase/>);
 // the marquee renders three passes so the loop seam never lands on screen;
 // only the first pass is exposed to assistive tech
 const cards=container.querySelectorAll('.reel-card');
 expect(cards.length).toBe(18);
 expect([...cards].filter(c=>c.getAttribute('aria-hidden')!=='true').length).toBe(6);
 expect(container.textContent).toContain('Honest about limits');
 expect(container.textContent).toContain('INFEASIBLE');
});
it('renders lab controls without a backend',()=>{
 const {container}=render(<Lab/>);
 expect(screen.getByRole('button',{name:/Run measured batch/i})).toBeTruthy();
 expect(container.textContent).toContain('allocator');
});
