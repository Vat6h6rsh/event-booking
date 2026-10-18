const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2 })
export const formatMoney = (paise) => Number.isSafeInteger(paise) ? inr.format(paise / 100) : 'Unavailable'
export function rupeesToPaise(value) {
  const text = String(value).trim()
  if (!/^\d+(?:\.\d{1,2})?$/.test(text)) throw new Error('Enter a non-negative rupee amount with at most two decimals.')
  const [whole, fraction = ''] = text.split('.')
  const paise = Number(whole) * 100 + Number(fraction.padEnd(2, '0'))
  if (!Number.isSafeInteger(paise)) throw new Error('Amount is too large.')
  return paise
}
