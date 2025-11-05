export type TNavLink = {
  to?: string;
  label: string;
  icon?: JSX.Element;
  isActive?: boolean;
  isHidden?: boolean;
  children?: TNavLink[];
};
