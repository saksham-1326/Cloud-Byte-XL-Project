import {useCallback,useEffect,useRef,useState} from 'react';
import {API_BASE,requestJson} from '../api.js';
import {publishRepositoryData} from '../repositoryData.js';
import {validateRepositoryResponse} from '../integration.js';
import type {RepositoryResponse} from '../types';

export function useRepository() {
  const [snapshot,setSnapshot]=useState<RepositoryResponse|null>(null);
  const [pending,setPending]=useState(false);const [error,setError]=useState('');
  const [stale,setStale]=useState(false);const [history,setHistory]=useState<{at:string;score:number|null;findings:number}[]>([]);
  const controller=useRef<AbortController|null>(null);
  const lastRepository=useRef('');
  useEffect(()=>()=>controller.current?.abort(),[]);
  const analyze=useCallback(async(url:string,restore=false)=>{
    controller.current?.abort();const current=new AbortController();controller.current=current;
    setPending(true);setError('');
    try {
      const value=await requestJson(`${API_BASE}/api/github/repository${restore?'/latest':''}`,restore?{signal:current.signal}:{signal:current.signal,timeoutMs:180000,method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:url.trim()})});
      const data=validateRepositoryResponse(value) as RepositoryResponse;
      if(current.signal.aborted || controller.current!==current)return;
      const sameRepository=lastRepository.current===data.repository.url;
      lastRepository.current=data.repository.url;setSnapshot(data);
      publishRepositoryData(data);setStale(false);
      const entry={at:new Date().toISOString(),score:data.analysis?.overall??null,findings:data.analysis?.issues?.length??0};
      setHistory(rows=>data.analysis?[entry,...(sameRepository?rows:[])].slice(0,20):sameRepository?rows:[]);
    } catch(reason) {
      if(current.signal.aborted || controller.current!==current)return;
      setError(reason instanceof Error?reason.message:'Repository request failed.');setStale(true);
    } finally {if(controller.current===current)setPending(false);}
  },[]);
  return {snapshot,pending,error,stale,history,analyze};
}
