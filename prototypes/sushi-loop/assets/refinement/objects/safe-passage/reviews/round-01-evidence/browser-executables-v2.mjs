import {chromium} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),records=[];
for(const mode of ['chromium','shell']){
 console.log('EXECUTABLE_PROBE_BEGIN '+mode);const options=mode==='chromium'?{headless:true,channel:'chromium'}:{headless:true};const browser=await chromium.launch(options);
 try{const cdp=await browser.newBrowserCDPSession(),version=await cdp.send('Browser.getVersion');records.push({mode,launchOptions:options,browserVersion:browser.version(),CDPVersion:version,actualLaunchCommandLog:'browser-executables-v2.log',purpose:'Read-only actual executable/options launch-log probe with same exact launch configuration as independent12case replay; no additional media/candidate changes.'});}finally{await browser.close();}console.log('EXECUTABLE_PROBE_END '+mode);
}
fs.writeFileSync(path.join(here,'browser-executables-v2.json'),JSON.stringify({records,failedPriorProbe:'Browser.getBrowserCommandLine unavailable because automation flag not enabled; exact failed code/log retained, launch debuglog used instead.'},null,2)+'\n');
