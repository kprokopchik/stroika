// Печать HTML-листов в PDF через Chromium (Playwright). Вызывается из tools/make_pdf.py.
// node tools/pdf.js tmp/print/manifest.json
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const page = await browser.newPage();
  for (const j of jobs) {
    await page.setContent(fs.readFileSync(path.resolve(j.html), 'utf8'), { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const footer = `<div style="font: 7px Arial, sans-serif; color: #555; width: 100%; padding: 0 12mm; display: flex; justify-content: space-between;">
      <span>${j.footer.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</span>
      <span>лист <span class="pageNumber"></span> из <span class="totalPages"></span></span></div>`;
    await page.pdf({
      path: j.pdf, preferCSSPageSize: true, printBackground: true,
      displayHeaderFooter: true, headerTemplate: '<div></div>', footerTemplate: footer,
    });
    console.log(path.basename(j.pdf));
  }
  await browser.close();
})();
