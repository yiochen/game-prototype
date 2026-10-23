import {createServer} from 'vite';
import path from 'node:path';
import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const p=path.dirname(path.dirname(fileURLToPath(import.meta.url))),require=createRequire(import.meta.url);
const config={configFile:false,root:process.cwd(),cacheDir:path.join(p,'resources/toolchain/vite-cache'),server:{host:'127.0.0.1',port:5181,strictPort:true}};
const server=await createServer(config);await server.listen();
await fs.writeFile(path.join(p,'evidence/review-server.json'),JSON.stringify({node:process.version,vite:require('vite/package.json').version,config},null,2)+'\n');console.log('Independent review server listening127.0.0.1:5181');
