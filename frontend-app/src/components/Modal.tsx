import {useEffect,useRef,type ReactNode} from 'react';
import {Icon} from './Icon';
export function Modal({title,close,children,palette=false}:{title:string;close:()=>void;children:ReactNode;palette?:boolean}){
  const ref=useRef<HTMLDialogElement>(null);
  useEffect(()=>{const d=ref.current;if(!d)return;const previous=document.activeElement as HTMLElement|null;
    if(typeof d.showModal==='function')d.showModal();else d.setAttribute('open','');
    d.querySelector<HTMLElement>('input,button,select,a')?.focus();
    return()=>{if(typeof d.close==='function')d.close();previous?.focus();};},[]);
  return <dialog ref={ref} className={palette?'command-overlay modal-palette':'context-drawer open'} aria-label={title} onCancel={e=>{e.preventDefault();close();}} onClick={e=>{if(e.target===e.currentTarget)close();}}><div className={palette?'command-palette':'drawer-inner'}><header><strong>{title}</strong><button aria-label={`Close ${title}`} onClick={close}><Icon name="x"/></button></header>{children}</div></dialog>;
}
