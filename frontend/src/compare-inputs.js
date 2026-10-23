// A contiguous edit window is easier to inspect than a character-by-character
// diff for short payloads. Common prefix/suffix remain readable and unchanged.
export function editWindow(previous, current) {
  let start = 0;
  while (
    start < previous.length &&
    start < current.length &&
    previous[start] === current[start]
  )
    start++;
  let beforeEnd = previous.length,
    afterEnd = current.length;
  while (
    beforeEnd > start &&
    afterEnd > start &&
    previous[beforeEnd - 1] === current[afterEnd - 1]
  ) {
    beforeEnd--;
    afterEnd--;
  }
  return { start, beforeEnd, afterEnd };
}
