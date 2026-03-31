export function formatInr(value) {
  const numeric = Number(value || 0)
  if (numeric >= 10000000) return '₹' + (numeric / 10000000).toFixed(1) + ' Cr'
  if (numeric >= 100000) return '₹' + (numeric / 100000).toFixed(1) + ' L'
  return '₹' + numeric.toLocaleString('en-IN')
}

export function formatStrike(value) {
  return Number(value || 0).toLocaleString('en-IN')
}
