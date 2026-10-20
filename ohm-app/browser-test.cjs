const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(process.env.OHM_URL||'http://127.0.0.1:18763');
 await page.waitForFunction(()=>document.querySelector('#board').options.length===10);
 async function select(id,text){const value=await page.locator('#'+id+' option').evaluateAll((opts,text)=>opts.find(o=>o.textContent.startsWith(text)).value,text);await page.selectOption('#'+id,value);}
 await select('a','U1 6 ·');await select('b','U1 7 ·');
 if(!/100.00 kΩ/.test(await page.locator('#result').innerText()))throw Error('RF1 reading wrong');
 if(!/RF1/.test(await page.locator('#paths').innerText()))throw Error('No RF1 path');
 
 await page.click('#back');
 if(await page.locator('#back').getAttribute('aria-pressed')!=='true')throw Error('Back toggle');
 const countBack=await page.locator('#pcb .copper').count();if(!countBack)throw Error('Back empty');
 const mirrored=await page.evaluate(()=>{const p=board.pads.filter(visible).at(-1),n=[...document.querySelectorAll('#pcb .copper')].at(-1);return n.getAttribute('transform').startsWith('translate('+(board.bounds[0]+board.bounds[2]-p.x)+' '+p.y+')');});
 if(!mirrored)throw Error('Back coordinates not physically mirrored');
 await page.selectOption('#board','9');
 await select('a','RB6 1 ·');await select('b','RB6 2 ·');
 if(!/12.100 kΩ/.test(await page.locator('#result').innerText()))throw Error('Divider wrong '+await page.locator('#result').innerText());
 await page.click('#front');
 await page.click('#reset');
 const copper=page.locator('#pcb .copper').last();
 await copper.click({force:true});
 if(!/Place probe B/.test(await page.locator('#result').innerText()))throw Error('Copper click failed');
 await page.screenshot({path:'/tmp/pcbai-ohm-desktop.png'});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:'/tmp/pcbai-ohm-mobile.png',fullPage:true});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw Error('Mobile overflow');
 if(errors.length)throw Error(errors.join(';'));
 console.log(JSON.stringify({browser:'pass',boards:10,rf1:'100k',divider:'12.1k',backCopper:countBack,mobile:'pass'}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

