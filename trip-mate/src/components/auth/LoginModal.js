import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  Tab,
  Tabs,
  CircularProgress,
  IconButton,
  Link
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useAuth } from "../../auth/AuthContext";
import ForgotPasswordDialog from "./ForgotPasswordDialog";

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`auth-tabpanel-${index}`}
      aria-labelledby={`auth-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function LoginModal({ open, onClose, onSuccess }) {
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const { login, register } = useAuth();

  // Login form state
  const [loginData, setLoginData] = useState({
    email: "",
    password: ""
  });

  // Register form state
  const [registerData, setRegisterData] = useState({
    email: "",
    password: "",
    username: "",
    firstName: "",
    lastName: "",
    role: "USER"
  });

  const handleTabChange = (event, newValue) => {
    setTab(newValue);
    setError("");
  };

  const handleClose = () => {
    setError("");
    setTab(0);
    onClose();
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const result = await login(loginData.email, loginData.password);
    
    setLoading(false);
    
    if (result.success) {
      onSuccess?.();
      handleClose();
    } else {
      setError(result.message);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const result = await register(registerData);
    
    setLoading(false);
    
    if (result.success) {
      setTab(0); // Switch to login tab
      setError("");
      setRegisterData({
        email: "",
        password: "",
        username: "",
        firstName: "",
        lastName: "",
        role: "USER"
      });
      // Show success message or automatically switch to login
    } else {
      setError(result.message);
    }
  };

  const handleLoginChange = (field) => (e) => {
    setLoginData(prev => ({ ...prev, [field]: e.target.value }));
  };

  const handleRegisterChange = (field) => (e) => {
    setRegisterData(prev => ({ ...prev, [field]: e.target.value }));
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ position: 'relative', pb: 1 }}>
        <Typography variant="h4" component="div" sx={{ textAlign: 'center' }}>
          Welcome
        </Typography>
        <IconButton
          aria-label="close"
          onClick={handleClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      
      <DialogContent sx={{ px: 0, pb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <Tabs value={tab} onChange={handleTabChange} aria-label="auth tabs" centered>
            <Tab label="Sign In" />
            <Tab label="Sign Up" />
          </Tabs>
        </Box>

        <TabPanel value={tab} index={0}>
          <form onSubmit={handleLoginSubmit}>
            <Typography variant="h6" sx={{ mb: 2, textAlign: "center" }}>
              Welcome Back
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            <TextField
              fullWidth
              label="Email"
              type="email"
              value={loginData.email}
              onChange={handleLoginChange("email")}
              margin="normal"
              required
              disabled={loading}
            />

            <TextField
              fullWidth
              label="Password"
              type="password"
              value={loginData.password}
              onChange={handleLoginChange("password")}
              margin="normal"
              required
              disabled={loading}
            />

            <Box sx={{ mt: 1, textAlign: "right" }}>
              <Link
                component="button"
                type="button"
                variant="body2"
                onClick={(e) => {
                  e.preventDefault();
                  setShowForgotPassword(true);
                }}
                sx={{ cursor: "pointer" }}
              >
                Forgot Password?
              </Link>
            </Box>

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{ mt: 3 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : "Sign In"}
            </Button>
          </form>
        </TabPanel>

        <TabPanel value={tab} index={1}>
          <form onSubmit={handleRegisterSubmit}>
            <Typography variant="h6" sx={{ mb: 2, textAlign: "center" }}>
              Create Account
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            <TextField
              fullWidth
              label="Email"
              type="email"
              value={registerData.email}
              onChange={handleRegisterChange("email")}
              margin="normal"
              required
              disabled={loading}
            />

            <TextField
              fullWidth
              label="Username"
              value={registerData.username}
              onChange={handleRegisterChange("username")}
              margin="normal"
              required
              disabled={loading}
            />

            <Box sx={{ display: "flex", gap: 1 }}>
              <TextField
                fullWidth
                label="First Name"
                value={registerData.firstName}
                onChange={handleRegisterChange("firstName")}
                margin="normal"
                required
                disabled={loading}
              />

              <TextField
                fullWidth
                label="Last Name"
                value={registerData.lastName}
                onChange={handleRegisterChange("lastName")}
                margin="normal"
                required
                disabled={loading}
              />
            </Box>

            <TextField
              fullWidth
              label="Password"
              type="password"
              value={registerData.password}
              onChange={handleRegisterChange("password")}
              margin="normal"
              required
              disabled={loading}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{ mt: 3 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : "Sign Up"}
            </Button>
          </form>
        </TabPanel>
      </DialogContent>

      <ForgotPasswordDialog
        open={showForgotPassword}
        onClose={() => setShowForgotPassword(false)}
      />
    </Dialog>
  );
}