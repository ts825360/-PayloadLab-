// Temporary local review proxy. Not the default Vite configuration.
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],server:{host:'127.0.0.1',port:5174,strictPort:true,proxy:{'/api':{target:'http://127.0.0.1:8102',rewrite:(path)=>path.replace(/^\/api/,'')}}}});
