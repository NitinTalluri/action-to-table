import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import InfoIcon from "@mui/icons-material/Info";
import ReportIcon from "@mui/icons-material/Report";
import WarningIcon from "@mui/icons-material/Warning";
import { ListItem, ListItemText } from "@mui/material";
import IconButton from "@mui/material/IconButton";
import Skeleton from "@mui/material/Skeleton";
import { Fragment } from "react";

export type TReviewStatus = "success" | "error" | "warning" | "info";

export type TReviewedItem<Label = string, SubLabel = string> = {
  status: TReviewStatus;
  label: Label;
  subLabel: SubLabel;
};

export type TReviewListItemProps = TReviewedItem<string, string | string[]> & {
  onClick?: () => void;
};

export const ReviewListIcon = (status: TReviewStatus) => {
  switch (status) {
    case "error": {
      return <ReportIcon color="error" />;
    }
    case "info": {
      return <InfoIcon color="info" />;
    }
    case "success": {
      return <CheckCircleIcon color="success" />;
    }
    case "warning": {
      return <WarningIcon color="warning" />;
    }
    case undefined: {
      return <Skeleton variant="circular" width={24} height={24} />;
    }
    default: {
      throw new Error(`Unknown status ${status}`);
    }
  }
};

export const ReviewButton = (props: Omit<TReviewListItemProps, "subLabel">) => {
  const { status, onClick } = props;
  return (
    <IconButton onClick={onClick} disableRipple={onClick === undefined}>
      {ReviewListIcon(status)}
    </IconButton>
  );
};

export const ReviewListItem = (props: TReviewListItemProps) => {
  const { status, subLabel, label, onClick } = props;
  if (Array.isArray(subLabel)) {
    const brLabels = subLabel.map((label) => (
      <Fragment key={label}>
        {label}
        <br />
      </Fragment>
    ));
    return (
      <ListItem disableGutters>
        <ReviewButton label={label} status={status} onClick={onClick} />
        <ListItemText primary={label} secondary={brLabels} />
      </ListItem>
    );
  }
  return (
    <ListItem disableGutters>
      <ReviewButton label={label} status={status} onClick={onClick} />
      <ListItemText primary={label} secondary={subLabel} />
    </ListItem>
  );
};
