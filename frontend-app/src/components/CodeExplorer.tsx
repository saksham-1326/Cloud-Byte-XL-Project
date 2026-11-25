import {useEffect,useState} from 'react';
import {API_BASE,requestJson} from '../api.js';
import {sourceLink} from '../integration.js';
import type {RepositoryResponse} from '../types';
import {EmptySignal,Panel,PanelHeader} from './Primitives';
import {Notice} from './DataUI';
interface Props {paths:string[];repository:RepositoryResponse['repository'];title?:string}
export function CodeExplorer(props:Props){return <Explorer key={`${props.repository.url}:${props.repository.analysisCommitSha||props.repository.branch}`} {...props}/>;}
function Explorer({paths,repository,title='Source explorer'}:Props){
  const [query,setQuery]=useState('');const [selected,setSelected]=useState('');const [retry,setRetry]=useState(0);
  const [folders,setFolders]=useState<string[]>([]);const [source,setSource]=useState<{path:string;text:string;error:string}|null>(null);
  const filtered=paths.filter(p=>p.toLowerCase().includes(query.toLowerCase()));
  useEffect(()=>{if(!selected)return;const controller=new AbortController();
    requestJson(`${API_BASE}/api/github/file`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:repository.url,path:selected,branch:repository.analysisCommitSha||repository.branch}),signal:controller.signal})
      .then(value=>{if(!controller.signal.aborted)setSource({path:selected,text:typeof value.content==='string'?value.content:'',error:''});})
      .catch(e=>{if(!controller.signal.aborted)setSource({path:selected,text:'',error:e.message});});
    return()=>controller.abort();
  },[repository.url,repository.analysisCommitSha,repository.branch,selected,retry]);
  const topFolders=[...new Set(filtered.filter(p=>p.includes('/')).map(p=>p.split('/')[0]))];
  const link=selected?sourceLink(repository,selected,undefined):undefined;
  return <div className="ide-workspace integrated-explorer"><Panel className="file-explorer"><PanelHeader kicker="REPOSITORY" title={title}/><div className="panel-body"><input aria-label="Search repository files" placeholder="Find a file…" value={query} onChange={e=>setQuery(e.target.value)}/><div className="real-file-tree">{topFolders.map(folder=><div key={folder}><button aria-expanded={folders.includes(folder)||Boolean(query)} onClick={()=>setFolders(v=>v.includes(folder)?v.filter(x=>x!==folder):[...v,folder])}>▸ {folder}</button>{(folders.includes(folder)||query)&&filtered.filter(p=>p.startsWith(folder+'/')).map(p=><button className={selected===p?'selected':''} key={p} onClick={()=>{setSource(null);setSelected(p);setRetry(v=>v+1);}}>{p.slice(folder.length+1)}</button>)}</div>)}{filtered.filter(p=>!p.includes('/')).map(p=><button className={selected===p?'selected':''} key={p} onClick={()=>{setSource(null);setSelected(p);setRetry(v=>v+1);}}>{p}</button>)}{!filtered.length&&<p>No matching files.</p>}</div></div></Panel><Panel className="code-editor"><div className="editor-tabs"><span className="active">{selected||'No file selected'}</span>{link&&<a href={link} target="_blank" rel="noopener noreferrer">Open on GitHub ↗</a>}</div>{!selected?<EmptySignal icon="code" title="Select a source file" copy="Expand a folder or search the authentic repository tree."/>:source?.path!==selected?<div className="panel-body" role="status">Loading source…</div>:source.error?<div className="panel-body"><Notice error>{source.error}</Notice><button onClick={()=>{setSource(null);setRetry(v=>v+1);}}>Retry file</button></div>:<pre className="source-code" tabIndex={0}>{source.text||'This file is empty.'}</pre>}<div className="editor-status"><span>Read only</span><span>{repository.analysisCommitSha?.slice(0,12)||repository.branch}</span></div></Panel></div>;
}
