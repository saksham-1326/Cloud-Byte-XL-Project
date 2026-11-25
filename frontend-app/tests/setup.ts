import {afterEach,vi} from 'vitest';
import {cleanup} from '@testing-library/react';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
Object.defineProperty(window,'matchMedia',{writable:true,value:vi.fn().mockImplementation(()=>({matches:false,addEventListener:vi.fn(),removeEventListener:vi.fn()}))});
window.scrollTo=vi.fn();
HTMLElement.prototype.scrollIntoView=vi.fn();
