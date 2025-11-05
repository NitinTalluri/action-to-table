import * as React from "react";

/** Inner component sees K as required & non-nullable */
type NonNullProps<P, K extends keyof P> = Omit<P, K> & {
  [Q in K]-?: NonNullable<P[Q]>;
};

/** Wrapped boundary allows K to be optional and nullish */
type LoosenProps<P, K extends keyof P> = Omit<P, K> & {
  [Q in K]?: P[Q] | null | undefined;
};

/**
 * Type guard: proves that `obj[k]` is neither null nor undefined for all k in K.
 * After this returns true, TS narrows `obj` to include required, non-nullable K props.
 */
const hasNonNull = <P, K extends readonly (keyof P)[]>(
  obj: P,
  keys: K,
): obj is P & { [Q in K[number]]-?: NonNullable<P[Q]> } => {
  // runtime check
  return keys.every((k) => obj[k] !== null && obj[k] !== undefined);
};

/**
 * HOC: write the inner component against NonNullProps so it's free of null checks.
 * Export the wrapped version that accepts nullish K and shows a fallback until ready.
 */
export const withRequiredProps = <P, K extends readonly (keyof P)[]>(
  Comp: React.ComponentType<NonNullProps<P, K[number]>>,
  keys: K,
): React.FC<LoosenProps<P, K[number]> & { fallback: React.ReactNode }> => {
  const Guarded: React.FC<
    LoosenProps<P, K[number]> & { fallback: React.ReactNode }
  > = (props) => {
    const { fallback, ...rest } = props;

    // Treat the remainder as the original P shape (safe: it's still the same fields)
    const candidate = rest as P;

    if (!hasNonNull(candidate, keys)) {
      return <>{fallback}</>;
    }

    // At this point `candidate` is narrowed to:
    // P & { [Q in K[number]]-?: NonNullable<P[Q]> }
    // which is structurally compatible with NonNullProps<P, K[number]>.
    return <Comp {...candidate} />;
  };

  Guarded.displayName = `withRequiredProps(${Comp.displayName ?? Comp.name ?? "Component"})`;
  return Guarded;
};
