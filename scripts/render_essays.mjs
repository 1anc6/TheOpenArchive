// Render the designed essay HTML in essay-sources/<id>/index.html to source-pdfs/<id>.pdf.
//   node scripts/render_essays.mjs              # all essays that have a source
//   node scripts/render_essays.mjs secret-santa # just these
// Needs Playwright. Set PLAYWRIGHT_PATH to its folder if it isn't installed in this project.
import { createRequire } from "node:module";
import { pathToFileURL, fileURLToPath } from "node:url";
import { readdirSync, existsSync } from "node:fs";
import path from "node:path";

const require = createRequire(import.meta.url);
const pwPath = process.env.PLAYWRIGHT_PATH || "playwright";
const { chromium } = require(pwPath);

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcDir = path.join(root, "essay-sources");
let ids = process.argv.slice(2);
if (!ids.length) ids = readdirSync(srcDir).filter((d) => existsSync(path.join(srcDir, d, "index.html")));

const browser = await chromium.launch();
for (const id of ids) {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(path.join(srcDir, id, "index.html")).href, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => window.__ready ?? true);
  await page.waitForTimeout(400);
  const out = path.join(root, "source-pdfs", `${id}.pdf`);
  await page.pdf({ path: out, preferCSSPageSize: true, printBackground: true });
  console.log("wrote", path.relative(root, out));
  await page.close();
}
await browser.close();
