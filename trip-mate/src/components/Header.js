import { useEffect, useState } from "react";
import { useParams, useSearchParams, useLocation, useNavigate, Link } from "react-router-dom";
import { travelIcon } from '../assets';
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import LoginModal from "./auth/LoginModal";
import { useAuth } from "../auth/AuthContext";

const TITLE = "Travel Planner";
export default function Header() {
  const { user, logout } = useAuth();
  const [loginModalOpen, setLoginModalOpen] = useState(false);

  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [title, setTitle] = useState(TITLE);

  useEffect(() => {
    if (location.pathname.startsWith(`/plan/${id}`)) {
      const destination = searchParams.get("destination");
      destination && setTitle(`Trip to ${destination}`);
    } else {
      setTitle(TITLE);
    }
  }, [location, id, searchParams]);

  const handleSignInClick = () => {
    setLoginModalOpen(true);
  };

  return (
    <>
      <AppBar position="fixed" color="transparent" elevation={0}>
        <Toolbar>
          <Box
            component="img"
            src={travelIcon}
            alt="Logo"
            sx={{ width: 28, height: 28, marginRight: 1, objectFit: 'cover', cursor: 'pointer' }}
            onClick={() => navigate("/")}
          />
          <Typography variant="h3" sx={{ flexGrow: 1, fontWeight: 700 }}>
            {title}
          </Typography>

          {user ? (
            <>
              <Button color="inherit" component={Link} to="/setup" sx={{ mr: 2 }}>
                Create a Trip
              </Button>
              <Button color="inherit" component={Link} to="/chat" sx={{ mr: 2 }}>
                Ask AI
              </Button>
              <Button color="inherit" component={Link} to="/plan" sx={{ mr: 8 }}>
                Trips
              </Button>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Button color="inherit" onClick={logout}>Logout</Button>
              </Box>
            </>
          ) : (
            <Button color="inherit" onClick={handleSignInClick}>
              Sign in
            </Button>
          )}
        </Toolbar>
      </AppBar>

      <LoginModal 
        open={loginModalOpen} 
        onClose={() => setLoginModalOpen(false)}
        onSuccess={() => setLoginModalOpen(false)}
      />
    </>
  );
}