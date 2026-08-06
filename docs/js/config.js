// Single source for every deployment-dependent value.
// Paths resolve relative to this module, so the site works both at the
// published URL and under a local `python3 -m http.server` from docs/.
export const DATA_BASE = new URL('../data/', import.meta.url).href;
export const BASE = new URL('../', import.meta.url).pathname;
export const ARXIV_ID = 'arXiv:XXXX.XXXXX';
export const ARXIV_URL = 'https://arxiv.org/abs/XXXX.XXXXX';
export const REPO_URL = 'https://github.com/ki-smile/post-training-taxonomy';
export const SITE_URL = 'https://ki-smile.github.io/post-training-taxonomy/';
export const TAX_VERSION = '1.0.0';
