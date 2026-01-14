import React, { useEffect, useState, useMemo } from "react";
import { Backdrop, CircularProgress, Box, Typography, Fade } from "@mui/material";

export default function GlobalLoadingOverlay({
  open,
  intervalMs = 3000,
  messages = [
    "This may take some time. Please hold on."
  ],
}) {
  const safeMessages = useMemo(
    () => (messages.length > 0 ? messages : ["Loading…"]),
    [messages]
  );
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    if (!open) return;
    const t = setInterval(() => setIdx((i) => (i + 1) % safeMessages.length), intervalMs);
    return () => clearInterval(t);
  }, [open, intervalMs, safeMessages.length]);

  useEffect(() => {
    if (open) setIdx(0);
  }, [open]);

  return (
    <Backdrop
      open={open}
      sx={{
        color: "#fff",
        zIndex: (theme) => theme.zIndex.drawer + 1000,
        flexDirection: "column",
        textAlign: "center",
        p: 3,
      }}
    >
      <CircularProgress color="inherit" />
      <Box mt={2} aria-live="polite" aria-atomic="true">
        {/* Trigger Fade animation by changing the key */}
        <Fade in key={idx} timeout={400}>
          <Typography variant="h6" color="#fff">{safeMessages[idx]}</Typography>
        </Fade>
      </Box>
    </Backdrop>
  );
}


