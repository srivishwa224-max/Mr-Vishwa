// Requires Playwright plus Chromium. Run against a fresh, disposable local database.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const {execFileSync}=require('node:child_process');
if(!process.env.REFERDUE_TEST_DB) throw new Error('Set REFERDUE_TEST_DB to the fresh disposable database used by the test server');

async function assertAccessibleViewport(page, label) {
  const result=await page.evaluate(() => {
    const visible=element => {
      const style=getComputedStyle(element);
      const box=element.getBoundingClientRect();
      return style.visibility!=='hidden' && style.display!=='none' && box.width>0 && box.height>0;
    };
    const accessibleName=element => {
      if(element.getAttribute('aria-label')?.trim()) return element.getAttribute('aria-label').trim();
      const labelledBy=element.getAttribute('aria-labelledby');
      if(labelledBy) return labelledBy.split(/\s+/).map(id=>document.getElementById(id)?.textContent||'').join(' ').trim();
      if(element.labels?.length) return [...element.labels].map(item=>item.textContent||'').join(' ').trim();
      return (element.textContent||element.value||element.title||'').trim();
    };
    const unnamed=[...document.querySelectorAll('button,input,select,textarea,a[href]')]
      .filter(visible).filter(element=>!accessibleName(element))
      .map(element=>element.outerHTML.slice(0,160));
    return {
      language:document.documentElement.lang,
      viewportMeta:document.querySelector('meta[name="viewport"]')?.content||'',
      unnamed,
      horizontalOverflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
      headings:[...document.querySelectorAll('h1')].filter(visible).length,
      liveStatus:document.querySelector('#message')?.getAttribute('role')||''
    };
  });
  assert.equal(result.language,'en',`${label}: document language must be declared`);
  assert.match(result.viewportMeta,/width=device-width/,`${label}: responsive viewport metadata is required`);
  assert.deepEqual(result.unnamed,[],`${label}: every visible control needs an accessible name`);
  assert.ok(result.horizontalOverflow<=1,`${label}: page overflows horizontally by ${result.horizontalOverflow}px`);
  assert.equal(result.headings,1,`${label}: exactly one visible level-one heading is required`);
  assert.equal(result.liveStatus,'status',`${label}: save/error messages need a status live region`);
}

async function assertKeyboardFocus(page,label) {
  await page.locator('body').press('Tab');
  const focus=await page.evaluate(() => {
    const active=document.activeElement;
    const style=getComputedStyle(active);
    return {tag:active?.tagName||'', outline:style.outlineStyle, width:style.outlineWidth, shadow:style.boxShadow};
  });
  assert.ok(['A','BUTTON','INPUT','SELECT','TEXTAREA'].includes(focus.tag),`${label}: Tab must reach an interactive control`);
  assert.ok(focus.outline!=='none' || focus.width!=='0px' || focus.shadow!=='none',`${label}: keyboard focus indicator must remain visible`);
}

(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage();
    const errors=[]; page.on('pageerror',error=>errors.push(error.message));
    await page.goto('http://127.0.0.1:4174');
    await assertAccessibleViewport(page,'desktop account screen');
    await assertKeyboardFocus(page,'desktop account screen');
    const email=`sample-${Date.now()}@example.com`;
    await page.locator('#login [name=email]').fill(email);
    await page.locator('#login [name=password]').fill('Synthetic-test-passphrase-only');
    await page.locator('#login button[value=register]').click();
    await page.waitForFunction(()=>document.querySelector('#message').textContent==='Saved.');
    // Test-only mailbox access to this disposable database; never use a real database.
    const script="import sqlite3,sys; db=sqlite3.connect(sys.argv[1]); body=db.execute(\"SELECT body FROM account_mail WHERE recipient=? AND status='pending'\",(sys.argv[2],)).fetchone()[0]; print(body.split('#verify=')[1].split()[0])";
    const verification=execFileSync('python3',['-c',script,process.env.REFERDUE_TEST_DB,email],{encoding:'utf8'}).trim();
    await page.locator('#account-complete [name=token]').fill(verification);
    await page.locator('#account-complete button[value=verify-account]').click();
    await page.locator('#workspace').waitFor({state:'visible'});
    await page.locator('#new-workspace [name=name]').fill('Browser sample');
    await page.locator('#new-workspace button').click();
    await page.locator('#details').waitFor({state:'visible'});
    await page.locator('#partner [name=name]').fill('Sample referrer');
    await page.locator('#partner [name=email]').fill('partner@example.com');
    await page.locator('#partner button').click();
    await page.waitForFunction(()=>document.querySelector('#partner-selection').options.length===1);
    const data={prospect:'Sample prospect',company:'Example Co',email:'prospect@example.com',service:'Design',introduced:'2026-10-10',estimate:'1000'};
    for(const [name,value] of Object.entries(data)) await page.locator(`#referral [name=${name}]`).fill(value);
    await page.locator('#referral button[value=new]').click();
    await page.locator('#terms').waitFor({state:'visible'});
    await page.locator('#terms [name=value]').fill('10');
    await page.locator('#terms button').click();
    await page.locator('#terms').waitFor({state:'hidden'});
    await page.locator('#accept-link').click();
    await page.waitForFunction(()=>document.querySelector('#generated-token').textContent.includes('#accept='));
    const text=await page.locator('#generated-token').textContent();
    const token=decodeURIComponent(text.split('#accept=')[1]);
    await page.locator('#capability [name=token]').fill(token);
    await page.locator('#capability button[value=accept-preview]').click();
    await page.locator('#accept-confirm').waitFor({state:'visible'});
    await page.locator('#accept-confirm').click();
    await page.waitForFunction(()=>document.querySelector('#ledger-summary').textContent.includes('Stage: Accepted'));
    await page.locator('#stage [name=stage]').selectOption('Won');
    await page.locator('#stage button').click();
    await page.waitForFunction(()=>document.querySelector('#ledger-summary').textContent.includes('Stage: Won'));
    await page.locator('#payment [name=amount]').fill('500');
    await page.locator('#payment button').click();
    await page.waitForFunction(()=>document.querySelector('#ledger-summary').textContent.includes('Pending approval'));
    await page.locator('#approval [name=due_date]').fill('2026-10-10');
    await page.locator('#approval button').click();
    await page.waitForFunction(()=>document.querySelector('#ledger-summary').textContent.includes('Due date: 2026-10-10'));
    await page.locator('#payment [name=kind]').selectOption('commission');
    await page.locator('#payment [name=amount]').fill('50');
    await page.locator('#payment button').click();
    await page.waitForFunction(()=>document.querySelector('#ledger-summary').textContent.includes('Commission Paid'));
    await page.reload();
    await page.waitForFunction(()=>document.querySelector('#ledger-summary').textContent.includes('Commission Paid'));
    await page.setViewportSize({width:390,height:844});
    await assertAccessibleViewport(page,'mobile completed workspace');
    await assertKeyboardFocus(page,'mobile completed workspace');
    assert.deepEqual(errors,[]);
    console.log('Browser workflow passed: account → introduction → acceptance → revenue → approval → payment → reload; desktop/mobile accessibility smoke checks passed.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
