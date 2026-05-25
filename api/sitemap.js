// ──────────────────────────────────────────────────────────────────
//  Dynamic Sitemap Generator — Vercel Serverless Function
//  Route:   GET /api/sitemap  (rewritten to /sitemap.xml via vercel.json)
//
//  HOW TO ADD A URL:
//    1. Open sitemap-config.json
//    2. Add an object to the "urls" array:
//       { "path": "/works/my-new-tool.html", "priority": 0.85, "label": "My New Tool" }
//    3. Push to GitHub — the sitemap updates automatically on next deploy
//
//  HOW TO DELETE A URL:
//    Remove its object from sitemap-config.json and push.
// ──────────────────────────────────────────────────────────────────

const path = require('path');
const fs   = require('fs');

module.exports = async function handler(req, res) {
  // Only allow GET
  if (req.method !== 'GET') {
    return res.status(405).end('Method Not Allowed');
  }

  // Read config (bundled at deploy time)
  const configPath = path.join(process.cwd(), 'sitemap-config.json');
  let config;
  try {
    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch (e) {
    return res.status(500).end('sitemap-config.json not found or invalid');
  }

  const { baseUrl, defaultChangefreq, defaultPriority, urls } = config;

  // Build lastmod from today (UTC)
  const today = new Date().toISOString().split('T')[0];

  // Build XML
  const urlEntries = urls.map(entry => {
    const loc        = `${baseUrl}${entry.path}`;
    const lastmod    = entry.lastmod || today;
    const changefreq = entry.changefreq || defaultChangefreq;
    const priority   = entry.priority  ?? defaultPriority;
    const comment    = entry.label ? `  <!-- ${entry.label} -->` : '';
    return `${comment}
  <url>
    <loc>${loc}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority.toFixed(1)}</priority>
  </url>`;
  }).join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
    http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
${urlEntries}
</urlset>`;

  res.setHeader('Content-Type', 'application/xml; charset=utf-8');
  res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate');
  return res.status(200).end(xml);
};
