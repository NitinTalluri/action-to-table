export const objectKeys = <Obj extends object>(obj: Obj): (keyof Obj)[] => {
  /**
   * Helps to get the keys of an object and types them as the keys of the object
   */
  return Object.keys(obj) as (keyof Obj)[];
};
