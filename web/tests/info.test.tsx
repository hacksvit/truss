import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import Info from '../src/routes/Info';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('keeps mobile chapter navigation usable when reduced motion hides the pinned scene',()=>{
 vi.stubGlobal('innerWidth',390);
 vi.stubGlobal('matchMedia',()=>({matches:true,addEventListener:()=>{},removeEventListener:()=>{}}));
 const scroll=vi.fn();vi.stubGlobal('scrollTo',scroll);
 render(<Info/>);
 fireEvent.click(screen.getByRole('button',{name:'The bigger picture'}));
 expect(scroll).toHaveBeenCalledWith({top:expect.any(Number),behavior:'instant'});
 expect(Number.isFinite(scroll.mock.calls[0][0].top)).toBe(true);
 expect(screen.getByRole('region',{name:'Tested Today'}).textContent).toContain('not the whole network');
 expect(screen.getByRole('link',{name:'Walk the example ↗'}).getAttribute('href')).toBe('/example');
});
