import { APP_BASE_HREF } from '@angular/common';
import { renderApplication } from '@angular/platform-server';
import express from 'express';
import { existsSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';
import 'zone.js/node';
import bootstrap from '../src/main.server';

const __dirname = dirname(fileURLToPath(import.meta.url));
const browserDistFolder = resolve(__dirname, '../browser');
const indexHtml = existsSync(join(browserDistFolder, 'index.original.html'))
  ? join(browserDistFolder, 'index.original.html')
  : join(browserDistFolder, 'index.html');

const app = express();

// Serve static files
app.use(express.static(browserDistFolder, {
  maxAge: '1y',
  index: false
}));

// Handle all other routes with Angular SSR
app.get('*', async (req, res, next) => {
  try {
    const html = await renderApplication(bootstrap, {
      document: indexHtml,
      url: req.originalUrl,
      platformProviders: [{ provide: APP_BASE_HREF, useValue: req.baseUrl }]
    });
    res.send(html);
  } catch (err) {
    next(err);
  }
});

// Start the server
if (process.env['NODE_ENV'] !== 'test') {
  const port = process.env['PORT'] || 4000;
  app.listen(port, () => {
    console.log(`Server listening on http://localhost:${port}`);
  });
}

export default app;
