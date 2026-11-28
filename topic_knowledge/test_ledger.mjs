import {readFileSync} from 'node:fs';
import {runTests} from './ledger.mjs';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const result=runTests(read('./registry.json'),read('../topics/T001/v3_FINAL_REVIEW.json'),read('../topics/T001/v2_RESEARCH.json'));
console.log(JSON.stringify(result.tests,null,2));
if(result.tests.some(x=>x.status!=='PASS'))process.exitCode=1;
