'use client';

/**
 * 在 hydration 之前运行的主题脚本。
 *
 * 读取 at-theme cookie；值为 system（或缺省）时用 prefers-color-scheme 解析，
 * 然后把解析结果写到 <html data-theme="light|dark">，避免首屏闪烁。
 */
const SCRIPT = `(function () {
  var m = document.cookie.match(/(?:^|;\\s*)at-theme=(light|dark|system)/);
  var saved = m ? m[1] : 'system';
  var dark = saved === 'dark' || (saved === 'system' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
})();`;

export function ThemeScript() {
  return <script dangerouslySetInnerHTML={{ __html: SCRIPT }} />;
}
