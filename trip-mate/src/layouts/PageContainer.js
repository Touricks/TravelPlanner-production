import React from "react";
import { Container, Box } from "@mui/material";
import { styled } from "@mui/material/styles";

const Root = styled(Box)(({ theme }) => ({
  minHeight: `calc(100vh - 56px)`,
  display: "flex",
  [theme.breakpoints.up("sm")]: {
    minHeight: `calc(100vh - 64px)`,
  },
}));

export default function PageContainer({
  children,
  maxWidth = "md",
  center = false,
  sx = {},
  ...props
}) {
  const Inner = (
    <Box
      sx={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        ...(center && { justifyContent: "center", alignItems: "center" }),
      }}
    >
      {children}
    </Box>
  );

  return (
    <Root sx={sx} {...props}>
      {maxWidth === false ? (
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
          {Inner}
        </Box>
      ) : (
        <Container maxWidth={maxWidth}>{Inner}</Container>
      )}
    </Root>
  );
}
