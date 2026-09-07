import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],server:{proxy:{'/console-api':{target:'http://127.0.0.1:8001',rewrite:path=>path.replace(/^\/console-api/,'/api')},'/console-ws':{target:'ws://127.0.0.1:8001',ws:true,rewrite:path=>path.replace(/^\/console-ws/,'/ws')},'/api':'http://127.0.0.1:8000','/ws':{target:'ws://127.0.0.1:8000',ws:true}}},test:{environment:'jsdom',include:['tests/**/*.test.{ts,tsx}']}});
