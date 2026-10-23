import {chromium} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),records=[];
for(const mode of ['chromium','shell']){
 const options=mode==='chromium'?{headless:true,channel:'chromium'}:{headless:true};const browser=await chromium.launch(options);const cdp=await browser.newBrowserCDPSession();const command=await cdp.send('Browser.getBrowserCommandLine'),version=await cdp.send('Browser.getVersion');
 records.push({mode,launchOptions:options,actualCommandLine:command.arguments,actualExecutable:command.arguments[0],browserVersion:browser.version(),CDPVersion:version,purpose:'Read-only actual executable/options probe with same exact launch configuration as independent12case replay; no additional media/candidate changes.'});await browser.close();
}
fs.writeFileSync(path.join(here,'browser-executables.json'),JSON.stringify({records},null,2)+'\n');console.log(JSON.stringify(records.map(r=>({mode:r.mode,actualExecutable:r.actualExecutable,version:r.browserVersion}))));
