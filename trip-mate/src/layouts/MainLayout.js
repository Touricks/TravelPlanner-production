import { Outlet } from "react-router-dom";
import { Box } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import Header from "../components/Header";

export default function MainLayout() {

  const theme = useTheme();
  return (
    <div>
      <Header />

      {/* Spacer using theme.mixins.toolbar to offset the AppBar */}
      <Box sx={theme.mixins.toolbar} />

      <div>
        <Outlet />
      </div>
    </div>
  );
}
