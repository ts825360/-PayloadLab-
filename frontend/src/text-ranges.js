// API ranges count Unicode code points; JavaScript slice uses UTF-16 offsets.
export function codepointRange(text, range) {
  const characters = Array.from(text);
  const clamp = (value, fallback) => Number.isFinite(value)
    ? Math.max(0, Math.min(characters.length, Math.trunc(value))) : fallback;
  const start = clamp(range?.start, 0);
  const end = Math.max(start, clamp(range?.end, characters.length));
  return {
    start: characters.slice(0, start).join('').length,
    end: characters.slice(0, end).join('').length,
  };
}
