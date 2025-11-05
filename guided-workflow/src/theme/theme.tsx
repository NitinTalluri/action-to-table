import { createTheme } from "@mui/material/styles";

import { fontFaces } from "~/theme/fonts";

const theme = createTheme({
  palette: {
    primary: {
      main: "rgb(25, 118, 210)",
    },
    secondary: {
      main: "#1e4471",
    },
    success: {
      main: "#6abf4b",
    },
    error: {
      main: "#e2231a",
    },
    warning: {
      main: "#fbab18",
    },
    info: {
      main: "#00bceb",
    },
    background: {
      default: "#ffffff",
      paper: "#ffffff",
    },
    text: {
      primary: "rgba(0,0,0,0.95)",
      secondary: "#495057",
    },
    grey: {
      50: "#f8fafc",
      100: "#f1f5f9",
      200: "#e2e8f0",
      300: "#cbd5e1",
      400: "#94a3b8",
      500: "#64748b",
      600: "#475569",
      700: "#334155",
      800: "#1e293b",
      900: "#0f172a",
    },
    contrastThreshold: 3,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: fontFaces,
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: "1rem",
        },
      },
    },
  },
  typography: {
    fontFamily: "Roboto",
    fontSize: 14,
  },
  transitions: {
    easing: {
      sharp: "cubic-bezier(0.4, 0, 0.6, 1)",
    },
    duration: {
      enteringScreen: 225,
    },
  },
});

export default theme;
