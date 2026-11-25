import {useCallback,useEffect,useRef,useState} from 'react';
import {API_BASE,requestJson} from '../api.js';
import type {Intelligence} from '../types';
import {validateIntelligenceResponse} from '../integration.js';
export function useIntelligence(repository:string,adminToken='') {
  const [result,setResult]=useState<{repository:string;data:Intelligence|null;error:string}>({repository:'',data:null,error:''});
  const [refreshing,setRefreshing]=useState(false);const active=useRef<AbortController|null>(null);
  const load=useCallback(async(signal:AbortSignal)=>{
    try {
      const response=await requestJson(`${API_BASE}/api/ai/v1/overview?repository=${encodeURIComponent(repository)}`,{signal,headers:adminToken?{'X-AI-Admin':adminToken}:{}});
      const data=validateIntelligenceResponse(response.data,repository) as Intelligence;
      if(!signal.aborted)setResult({repository,data,error:''});
    } catch(error){if(!signal.aborted)setResult({repository,data:null,error:error instanceof Error?error.message:'AI history unavailable.'});}
    finally{if(!signal.aborted)setRefreshing(false);}
  },[repository,adminToken]);
  useEffect(()=>{
    if(!repository)return;
    const controller=new AbortController();active.current=controller;void load(controller.signal);
    return()=>{controller.abort();active.current?.abort();};
  },[repository,load]);
  // Re-read historical intelligence while the dashboard is open. No write or
  // provider request is issued from a public browser.
  useEffect(()=>{
    if(!repository)return;
    let current:AbortController|null=null;
    const interval=setInterval(()=>{
      if(document.visibilityState==='hidden')return;
      current?.abort();current=new AbortController();void load(current.signal);
    },60000);
    return()=>{clearInterval(interval);current?.abort();};
  },[repository,load]);
  const refresh=()=>{if(!repository)return;active.current?.abort();const controller=new AbortController();active.current=controller;setRefreshing(true);void load(controller.signal);};
  return {data:result.repository===repository?result.data:null,error:result.repository===repository?result.error:'',loading:Boolean(repository)&&(refreshing||result.repository!==repository),refresh};
}
