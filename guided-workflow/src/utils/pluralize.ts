export const pluralize = (
  word: string,
  count: number,
  includeCount = false,
) => {
  const suffix = count === 1 ? "" : "s";
  return includeCount ? `${count} ${word}${suffix}` : `${word}${suffix}`;
};
