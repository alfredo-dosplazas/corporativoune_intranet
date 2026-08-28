export const formatMoney = (value: number) => {
    return value > 0 ? `$${value.toLocaleString(undefined, {minimumFractionDigits: 2})}` : '-'
}