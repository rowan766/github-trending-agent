/**
 * 格式化时间字符串为 "YYYY-MM-DD HH:mm:ss"
 * @param {string} raw - ISO 格式时间字符串，如 "2026-02-17T12:47:16.472160"
 * @returns {string}
 */
export function formatTime(raw) {
  if (!raw) return ''
  const d = new Date(raw)
  if (isNaN(d.getTime())) return raw
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
