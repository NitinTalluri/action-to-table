import Close from "@mui/icons-material/Close";
import Search from "@mui/icons-material/Search";
import {
  Box,
  Dialog,
  DialogContent,
  IconButton,
  InputAdornment,
  TextField,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useEffect, useState } from "react";

export const SearchInput = ({
  value,
  onChange,
  placeholder,
  resultsCount,
}: {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  resultsCount?: number;
}) => {
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up("sm"));

  useEffect(() => {
    if (isDesktop && open) {
      setOpen(false);
    }
  }, [isDesktop, open]);

  if (!isDesktop) {
    return (
      <div>
        <Box sx={{ position: "relative" }}>
          <Tooltip title={placeholder || "Search..."}>
            <IconButton onClick={() => setOpen(true)}>
              <Search />
            </IconButton>
          </Tooltip>
          {value.length ? (
            <Box
              sx={(theme) => ({
                position: "absolute",
                width: 7.5,
                height: 7.5,
                background: theme.palette.primary.main,
                borderRadius: "50%",
                top: 2.5,
                right: 2.5,
              })}
            />
          ) : null}
        </Box>
        <Dialog
          open={open}
          onClose={() => setOpen(false)}
          fullWidth
          sx={{
            "& .MuiDialog-container": {
              alignItems: "start",
            },
          }}
        >
          <DialogContent>
            <TextField
              fullWidth
              name="search"
              size="small"
              variant="outlined"
              placeholder={placeholder ?? "Search..."}
              onKeyDown={(e) => {
                // if enter key is pressed, close the dialog
                if (e.key === "Enter") {
                  e.preventDefault();
                  setOpen(false);
                }
              }}
              onChange={(e) => onChange(e.target.value)}
              value={value}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                  endAdornment: value.trim().length ? (
                    <>
                      {typeof resultsCount === "number" ? (
                        <InputAdornment position="start">
                          <Typography
                            variant="caption"
                            sx={{
                              margin: 0,
                            }}
                          >
                            {resultsCount}{" "}
                            {resultsCount === 1 ? "result" : "results"}
                          </Typography>
                        </InputAdornment>
                      ) : null}
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="Clear search"
                          onClick={() => onChange("")}
                        >
                          <Close />
                        </IconButton>
                      </InputAdornment>
                    </>
                  ) : null,
                },
              }}
            />
          </DialogContent>
        </Dialog>
      </div>
    );
  }
  return (
    <TextField
      sx={{ minWidth: 300 }}
      name="search"
      size="small"
      variant="outlined"
      placeholder={placeholder ?? "Search..."}
      onChange={(e) => onChange(e.target.value)}
      value={value}
      slotProps={{
        input: {
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
          endAdornment: value.trim().length ? (
            <>
              {typeof resultsCount === "number" ? (
                <InputAdornment position="start">
                  <Typography
                    variant="caption"
                    sx={{
                      margin: 0,
                    }}
                  >
                    {resultsCount} {resultsCount === 1 ? "result" : "results"}
                  </Typography>
                </InputAdornment>
              ) : null}
              <InputAdornment position="end">
                <IconButton
                  aria-label="Clear search"
                  onClick={() => onChange("")}
                >
                  <Close />
                </IconButton>
              </InputAdornment>
            </>
          ) : null,
        },
      }}
    />
  );
};
