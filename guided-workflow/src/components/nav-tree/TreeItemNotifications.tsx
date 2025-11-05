import { Chip, Stack, Tooltip } from "@mui/material";
import { MouseEvent } from "react";

import { TDetailNotification } from "~/domain/Workflows";
import { pluralize } from "~/utils/pluralize";

import { chipColor, TFilters } from "./utils";

export const TreeItemNotifications = ({
  notifications,
  onClick,
}: {
  notifications?: Record<TDetailNotification["notification_category"], number>;
  onClick?: (category: TFilters["category"][number]) => void;
}) => {
  const handleClick = (
    e: MouseEvent,
    category: TFilters["category"][number],
  ) => {
    // parent is either a link or button that we don't want to trigger
    e.stopPropagation();
    e.preventDefault();
    onClick?.(category);
  };

  return (
    <Stack direction="row" spacing="-.5rem">
      {notifications?.pending ? (
        <Tooltip title={pluralize("pending", notifications.pending, true)}>
          {onClick ? (
            <Chip
              onClick={(e) => handleClick(e, "pending")}
              label={notifications.pending}
              size="small"
              color={chipColor.pending}
            />
          ) : (
            <Chip
              label={notifications.pending}
              size="small"
              color={chipColor.pending}
            />
          )}
        </Tooltip>
      ) : null}
      {notifications?.result ? (
        <Tooltip title={pluralize("result", notifications.result, true)}>
          {onClick ? (
            <Chip
              onClick={(e) => handleClick(e, "result")}
              label={notifications.result}
              size="small"
              color={chipColor.result}
            />
          ) : (
            <Chip
              label={notifications.result}
              size="small"
              color={chipColor.result}
            />
          )}
        </Tooltip>
      ) : null}
      {notifications?.task ? (
        <Tooltip title={pluralize("task", notifications.task, true)}>
          {onClick ? (
            <Chip
              onClick={(e) => handleClick(e, "task")}
              label={notifications.task}
              size="small"
              color={chipColor.task}
            />
          ) : (
            <Chip
              label={notifications.task}
              size="small"
              color={chipColor.task}
            />
          )}
        </Tooltip>
      ) : null}
      {notifications?.error ? (
        <Tooltip title={pluralize("error", notifications.error, true)}>
          {onClick ? (
            <Chip
              onClick={(e) => handleClick(e, "error")}
              label={notifications.error}
              size="small"
              color={chipColor.error}
            />
          ) : (
            <Chip
              label={notifications.error}
              size="small"
              color={chipColor.error}
            />
          )}
        </Tooltip>
      ) : null}
    </Stack>
  );
};
