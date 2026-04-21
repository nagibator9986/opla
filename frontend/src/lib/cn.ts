export type ClassValue =
  | string
  | number
  | null
  | undefined
  | false
  | Record<string, boolean | null | undefined>
  | ClassValue[]

function push(acc: string[], value: ClassValue): void {
  if (!value) return
  if (typeof value === 'string' || typeof value === 'number') {
    acc.push(String(value))
    return
  }
  if (Array.isArray(value)) {
    for (const v of value) push(acc, v)
    return
  }
  if (typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) {
      if (v) acc.push(k)
    }
  }
}

// Zero-dep class joiner. Good enough without tailwind-merge — callers should
// keep variant order so later classes naturally override earlier ones.
export function cn(...inputs: ClassValue[]): string {
  const acc: string[] = []
  for (const input of inputs) push(acc, input)
  return acc.join(' ')
}
