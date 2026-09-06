import {it,expect,afterEach} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import Showcase from '../src/routes/Showcase';
import Lab from '../src/routes/Lab';
import BoundaryBanner from '../src/components/BoundaryBanner';
afterEach(cleanup);
it('identifies the mock and prototype boundary',()=>{
 const {container}=render(<><BoundaryBanner/><Showcase/></>);
 expect(container.textContent).toContain('MOCK');
 expect(screen.getByRole('link',{name:/Explore the mock console/})).toBeTruthy();
 expect(container.textContent).toContain('No real appliances or medical devices');
});
it('renders lab controls without a backend',()=>{
 const {container}=render(<Lab/>);
 expect(screen.getByRole('button',{name:/Run measured batch/i})).toBeTruthy();
 expect(container.textContent).toContain('allocator');
});
