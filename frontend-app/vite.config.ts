import {defineConfig,loadEnv} from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import process from 'node:process';
export default defineConfig(({command,mode})=>{
  if(command==='build'){
    const env={...loadEnv(mode,process.cwd(),'VITE_'),...process.env};
    const target=env.VITE_API_BASE_URL?new URL(env.VITE_API_BASE_URL):null;
    if(!target||target.protocol!=='https:'||['localhost','127.0.0.1','[::1]'].includes(target.hostname)||target.username||target.password||target.pathname!=='/'||target.search||target.hash)throw new Error('Production build requires VITE_API_BASE_URL=https://<approved-render-host>');
  }
  return {plugins:[react(),tailwindcss()]};
});
