export function invoiceTotal(lines) {
  return lines.reduce((total, line) => total + line.qty * line.unitPriceCents, 0);
}
