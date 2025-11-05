export function groupBy<V>(
  items: Array<V>,
  getter: (v: V) => string,
): Record<string, V[]> {
  const gMap = new Map<string, V[]>();
  items.forEach((item) => {
    const itemKey = getter(item);
    const currentValues = gMap.get(itemKey);
    if (!currentValues) {
      gMap.set(itemKey, [item]);
    } else {
      currentValues.push(item);
    }
  });
  return Object.fromEntries(gMap);
}
