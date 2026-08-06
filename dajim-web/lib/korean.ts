/** Picks the correct Korean particle (을/를, 은/는, 이/가, 과/와) for a word
 * ending in a syllable with or without a final consonant (받침). */
function hasBatchim(word: string): boolean {
  const lastChar = word.charCodeAt(word.length - 1);
  if (lastChar < 0xac00 || lastChar > 0xd7a3) return false;
  return (lastChar - 0xac00) % 28 !== 0;
}

export function withParticle(
  word: string,
  pair: [withBatchim: string, withoutBatchim: string],
): string {
  const [withB, withoutB] = pair;
  return `${word}${hasBatchim(word) ? withB : withoutB}`;
}

export const eulReul = (word: string) => withParticle(word, ["을", "를"]);
export const euroRo = (word: string) => withParticle(word, ["으로", "로"]);
