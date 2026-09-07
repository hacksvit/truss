import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import Example from '../src/routes/Example';
vi.mock('../src/components/SiteScene',()=>({default:({budgets,onMode}:{budgets:number[];onMode:(mode:'overview'|'explore')=>void})=><div><output aria-label="Scene proposals">{budgets.join(',')}</output><button onClick={()=>onMode('explore')}>Walk</button><button onClick={()=>onMode('overview')}>Overview</button></div>}));
afterEach(cleanup);
it('updates all three scene and control proposals when supply changes, including B above 350 W',()=>{
 const {container}=render(<Example/>);
 expect(screen.getByLabelText('Scene proposals').textContent).toBe('556,566,576');
 fireEvent.change(screen.getByRole('slider'),{target:{value:'2400'}});
 expect(screen.getByLabelText('Scene proposals').textContent).toBe('756,766,776');
 expect(container.querySelector('.grants')?.textContent).toContain('B766 W proposed');
 fireEvent.change(screen.getByRole('slider'),{target:{value:'3200'}});
 expect(screen.getByLabelText('Scene proposals').textContent).toBe('990,1040,1070');
});
it('reports an infeasible supply without presenting new grants',()=>{
 const {container}=render(<Example/>);
 fireEvent.change(screen.getByRole('slider'),{target:{value:'400'}});
 expect(container.querySelector('.grants')?.textContent).toBe('infeasible · short 210 W');
});
it('cascades the robot cloud away and rebuilds them after walking',()=>{
 const {container}=render(<Example/>);
 const clouds=container.querySelector('.cloud-stack')!;
 expect(clouds.children.length).toBe(1);
 expect(clouds.querySelector('img')?.getAttribute('src')).toBe('/clouds/cloud-robot.png');
 fireEvent.click(screen.getByRole('button',{name:'Walk'}));
 expect(clouds.classList.contains('clouds-away')).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:'Overview'}));
 expect(clouds.classList.contains('clouds-away')).toBe(false);
});
