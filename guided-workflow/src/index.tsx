import "./site.css";

import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import InfoIcon from "@mui/icons-material/Info";
import WarningIcon from "@mui/icons-material/Warning";
import { ThemeProvider } from "@mui/material";
import CssBaseline from "@mui/material/CssBaseline";
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { Amplify } from "aws-amplify";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { toast, Toaster } from "sonner";

import { isNotAuthenticatedError } from "~/utils/isNotAuthenticatedError";

import App from "./App";
import theme from "./theme/theme";
import isDev from "./utils/isDev";

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      if (isNotAuthenticatedError(error)) {
        toast.error("You are not authenticated. Please refresh the page.", {
          duration: 10000,
        });
      }
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      if (isNotAuthenticatedError(error)) {
        toast.error("You are not authenticated. Please refresh the page.", {
          duration: 10000,
        });
      } else {
        if (isDev) console.error(error);
      }
    },
  }),
  defaultOptions: {
    queries: {
      // default stale time of 300 ms for all queries
      staleTime: 300,
      retry: (failureCount, error) => {
        if (isDev) console.error(error);
        return failureCount <= 0;
      },
    },
  },
});

const maybeEnableMocking = async () => {
  if (
    !isDev ||
    !["true", "1"].includes(import.meta.env.VITE_MOCKING || "false")
  ) {
    return;
  }

  try {
    const mocks = import.meta.glob<Record<string, Record<string, () => void>>>(
      "../mocks/**",
    );
    const { worker } = await mocks["../mocks/worker.ts"]();
    return worker.start();
  } catch (error) {
    console.error("Failed to start mocking worker", error);
  }
};

Amplify.configure({
  Auth: {
    region: import.meta.env.VITE_AWS_REGION,
    userPoolId: import.meta.env.VITE_AMPLIFY_USERPOOL_ID,
    userPoolWebClientId: import.meta.env.VITE_AMPLIFY_WEBCLIENT,
    mandatorySignIn: true,
    oauth: {
      domain:
        import.meta.env.VITE_AWS_COGNITO_OAUTH_DOMAIN ||
        "datacanvas.auth.us-east-1.amazoncognito.com",
      scope: ["email", "profile", "aws.cognito.signin.user.admin", "openid"],
      redirectSignIn: import.meta.env.VITE_SSO_REDIRECT_URI,
      redirectSignOut: `${import.meta.env.VITE_SSO_REDIRECT_URI}/logout`,
      responseType: "code",
    },
  },
});

const container = document.getElementById("root")!;
const root = createRoot(container);

maybeEnableMocking().then(() =>
  root.render(
    <StrictMode>
      <ThemeProvider theme={theme}>
        <QueryClientProvider client={queryClient}>
          <CssBaseline />
          <App />
          <Toaster
            richColors
            icons={{
              success: <CheckCircleIcon />,
              error: <ErrorIcon />,
              info: <InfoIcon />,
              warning: <WarningIcon />,
            }}
          />
        </QueryClientProvider>
      </ThemeProvider>
    </StrictMode>,
  ),
);
