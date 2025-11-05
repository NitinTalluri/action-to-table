import { TreeItem } from "./TreeItem";
import { RenderTree, TFilters } from "./utils";

export const TreeNode = ({
  dc_user_id,
  nodes,
  expandedIds,
  filters,
}: {
  dc_user_id?: number;
  nodes: RenderTree;
  expandedIds: string[];
  filters: TFilters;
}) => {
  return (
    <TreeItem
      key={nodes.id}
      dc_user_id={dc_user_id}
      item={nodes}
      filters={filters}
      expanded={expandedIds.includes(nodes.id)}
    >
      {nodes.children?.map((node) => (
        <TreeNode
          key={node.id}
          dc_user_id={dc_user_id}
          expandedIds={expandedIds}
          nodes={node}
          filters={filters}
        />
      ))}
    </TreeItem>
  );
};
