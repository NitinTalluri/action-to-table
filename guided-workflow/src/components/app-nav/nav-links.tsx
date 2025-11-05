import AccessTimeIcon from "@mui/icons-material/AccessTime";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import ImportantDevicesIcon from "@mui/icons-material/ImportantDevices";
import PeopleIcon from "@mui/icons-material/People";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";

import { IAmplifyUser } from "~/domain/Users";

import { TNavLink } from "./utils";

// navLinks is a function that returns an array of TNavLink objects
// if the navLink has children, it will be rendered as a menu item with links for children
// if the navLink is hidden, it will not be rendered
export const navLinks = ({
  user,
  pathname,
}: {
  user: IAmplifyUser;
  pathname: string;
}): TNavLink[] => [
  {
    to: "engagements",
    label: "Engagements",
    icon: <PeopleIcon />,
    isActive:
      pathname.includes("engagements") ||
      (pathname.includes("workflows") && !pathname.includes("support")),
  },
  {
    to: "time-tracking",
    label: "Time Tracking",
    icon: <AccessTimeIcon />,
    isActive: pathname.includes("time-tracking"),
  },
  {
    label: "Financial Admin",
    isHidden: !user.isFinancialAdmin,
    icon: <AccountBalanceIcon />,
    isActive: pathname.includes("financial-admin"),
    children: [
      {
        to: "financial-admin/bookings",
        label: "Bookings",
        isActive: pathname.includes("financial-admin/bookings"),
      },
      {
        to: "financial-admin/revenue",
        label: "Revenue",
        isActive: pathname.includes("financial-admin/revenue"),
      },
      {
        to: "financial-admin/SEA",
        label: "SEA",
        isActive: pathname.includes("financial-admin/SEA"),
      },
    ],
  },
  {
    label: "Admin",
    isHidden: !user.isAdmin,
    icon: <AdminPanelSettingsIcon />,
    isActive: ["global-tagset", "templates", "admin"].includes(
      pathname.split("/")?.[1],
    ),
    children: [
      {
        to: "admin/global-tagset",
        label: "Global Tagset",
        isActive: pathname.includes("admin/global-tagset"),
      },
      {
        to: "admin/sdp",
        label: "Service Delivery Plan",
        isActive: pathname.includes("admin/sdp"),
      },
    ],
  },
  {
    label: "Manager Portal",
    isHidden: !(user.isManager || user.isAdmin || user.isPoolManager),
    icon: <ImportantDevicesIcon />,
    isActive: pathname.includes("manager-portal"),
    children: [
      {
        to:
          user.isManager || user.isAdmin
            ? "manager-portal/bookings/unclaimed"
            : "manager-portal/bookings/vendor",
        label: "Bookings",
        isActive: pathname.includes("bookings"),
      },
      {
        to: "manager-portal/pcv",
        label: "Parent Customer View",
        isHidden: !(user.isManager || user.isAdmin),
        isActive: pathname.includes("pcv"),
      },
    ],
  },
  {
    to: "support",
    label: "Support",
    icon: <SupportAgentIcon />,
    isActive: pathname.includes("support"),
  },
];
