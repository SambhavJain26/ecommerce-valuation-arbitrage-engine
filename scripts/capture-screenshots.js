const path = require('path');
const fs = require('fs');

// Resolve puppeteer-core from local or sibling node_modules
let puppeteer;
try {
  puppeteer = require('puppeteer-core');
} catch (e) {
  puppeteer = require(path.resolve(__dirname, '../../reddit-deep-research/node_modules/puppeteer-core'));
}

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE_URL = 'http://localhost:7860';
const OUTPUT_DIR = path.resolve(__dirname, '../docs/screenshots');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function run() {
  console.log('[Capture] Launching Chrome...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--window-size=1440,900']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });

    // 1. Capture Full Dashboard Overview
    console.log('[Capture] Navigating to Gradio Dashboard at ' + BASE_URL + '...');
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    try {
      await page.waitForSelector('#scrollContent, table, .dataframe', { timeout: 15000 });
    } catch (e) {
      console.log('[Capture] Selector wait reached timeout, continuing...');
    }
    await new Promise(r => setTimeout(r, 2500));

    console.log('[Capture] Capturing 01-dashboard-overview.png...');
    await page.screenshot({ path: path.join(OUTPUT_DIR, '01-dashboard-overview.png') });

    // 2. Focused View: Deals Table
    console.log('[Capture] Capturing 02-deal-opportunities-table.png...');
    const tableEl = await page.$('.table-wrap, table, .dataframe');
    if (tableEl) {
      await tableEl.screenshot({ path: path.join(OUTPUT_DIR, '02-deal-opportunities-table.png') });
    } else {
      await page.screenshot({ path: path.join(OUTPUT_DIR, '02-deal-opportunities-table.png') });
    }

    // 3. Focused View: Real-Time Execution Logs
    console.log('[Capture] Capturing 03-realtime-execution-logs.png...');
    const logsEl = await page.$('#logs_column, #scrollContent');
    if (logsEl) {
      await logsEl.screenshot({ path: path.join(OUTPUT_DIR, '03-realtime-execution-logs.png') });
    }

    // 4. Mobile Responsive View
    console.log('[Capture] Capturing 04-mobile-responsive-view.png...');
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true });
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    try {
      await page.waitForFunction(() => {
        const text = document.body ? document.body.innerText : '';
        return !text.includes('queue:') && text.includes('Deals found so far');
      }, { timeout: 35000 });
    } catch (e) {
      console.log('[Capture] Mobile wait timeout, proceeding...');
    }
    await new Promise(r => setTimeout(r, 1500));
    await page.screenshot({ path: path.join(OUTPUT_DIR, '04-mobile-responsive-view.png') });

    console.log('[Capture] All screenshots captured successfully in docs/screenshots/');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('[Capture Error]', err);
  process.exit(1);
});
