import { RenderTree } from "~/components/nav-tree/utils";
import { TSummaryNotification, TWorkflowTree } from "~/domain/Workflows";

export const assembleChildren = (
  tree: TWorkflowTree,
  id: number,
): RenderTree[] => {
  const branch = tree.find((node) => node.tree_id === id);
  if (!branch) return [];
  const children = tree.filter((node) =>
    branch.child_ids.includes(node.tree_id),
  );
  return children.map((child) => ({
    id: child.tree_id.toString(),
    name: child.action_label,
    ...(child.ui_enum ? { to: child.ui_enum } : {}),
    children: assembleChildren(tree, child.tree_id),
  }));
};

export const filterDuplicationsTree = (tree: RenderTree[]): RenderTree[] => {
  const filteredTree = tree.filter((node) => {
    const id = node.id;
    const appearsElsewhere = tree.some((node) =>
      node.children?.some((child) => child.id === id),
    );
    if (appearsElsewhere) {
      return false;
    }
    if (!node.children?.length) {
      return false;
    }
    return true;
  });
  return filteredTree;
};

export const sortTree = (tree: RenderTree[]): RenderTree[] => {
  // sort by name and then sort children recursively
  return tree
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((node) => {
      if (node.children) {
        node.children = sortTree(node.children);
      }
      return node;
    });
};

export const attachNotifications = (
  tree: RenderTree[],
  notifications: TSummaryNotification[],
): RenderTree[] => {
  return tree.map((node) => {
    const nodeNotifications = notifications.filter(
      (n) => n.tree_id === parseInt(node.id),
    );
    return {
      ...node,
      notifications: nodeNotifications,
      children: node.children
        ? attachNotifications(node.children, notifications)
        : undefined,
    };
  });
};
