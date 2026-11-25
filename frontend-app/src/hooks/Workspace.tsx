import {createContext,useContext} from 'react';
import type {useRepository} from './useRepository';
import type {useIntelligence} from './useIntelligence';
type Workspace = ReturnType<typeof useRepository> & {ai:ReturnType<typeof useIntelligence>;connect:()=>void;inspect:(id:string)=>void;adminToken:string;setAdminToken:(value:string)=>void;reviewedFindingIds:string[];markFindingReviewed:(id:string)=>void};
export const WorkspaceContext=createContext<Workspace|null>(null);
export function useWorkspace(){const value=useContext(WorkspaceContext);if(!value)throw new Error('Workspace provider required');return value;}
