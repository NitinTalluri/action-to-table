import { Box, capitalize, Paper, Stack, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";
import { z } from "zod";

import { isWorkflowUiEnum, WorkflowUiEnum } from "~/domain/Workflows";
import { SerialTaggingResultSchema } from "~/features/workflow-events/utils";
import { getEngagementNotificationsQuery } from "~/queries/workflows";
import { returnParsedData } from "~/utils/safeParse";

import { DefaultSchema } from "./util";

export const EventResult = () => {
  const { notificationId, engagementId, eventUiEnum } = useParams();

  const { data: notifications } = useQuery({
    ...getEngagementNotificationsQuery(Number(engagementId)),
    enabled: Boolean(engagementId),
  });

  const notification = notifications?.find(
    (n) => n.notification_id === Number(notificationId),
  );

  // takes in unknown data and returns parsed data based on the eventUiEnum
  const getParsedData = () => {
    if (!eventUiEnum || !isWorkflowUiEnum(eventUiEnum)) return;
    switch (eventUiEnum) {
      case WorkflowUiEnum.Enum["serial-tagging"]:
        return returnParsedData(notification?.data, SerialTaggingResultSchema);
      case WorkflowUiEnum.Enum["customer-upload"]:
        return returnParsedData(
          notification?.data,
          z.union([DefaultSchema, SerialTaggingResultSchema]),
        );
      case WorkflowUiEnum.Enum["collector-upload"]:
        return returnParsedData(notification?.data, SerialTaggingResultSchema);
      default:
        return returnParsedData(notification?.data, DefaultSchema);
    }
  };

  const parsedData = getParsedData();

  if (!parsedData) return null;
  if (Object.keys(parsedData).length === 0) return null;
  return (
    <Stack>
      <Typography variant="caption">Results Summary</Typography>
      <Paper sx={{ padding: 1 }}>
        {Object.entries(parsedData)
          // remove file link from the result summary
          // user can download the file from the ResultActions component
          ?.filter(([key]) => key !== "excel_location")
          ?.map(([key, value]) => (
            <Box
              key={key}
              sx={{
                display: "grid",
                gap: 1,
                gridTemplateColumns: "250px 1fr",
              }}
            >
              <Typography>{capitalize(key.split("_").join(" "))}</Typography>
              <Typography
                sx={{
                  fontWeight: "bold",
                }}
              >
                {value}
              </Typography>
            </Box>
          ))}
      </Paper>
    </Stack>
  );
};
