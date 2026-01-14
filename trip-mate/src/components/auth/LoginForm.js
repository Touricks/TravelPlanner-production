import { useState } from "react";
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  Paper,
  Tab,
  Tabs,
  CircularProgress
} from "@mui/material";
import { useAuth } from "../../auth/AuthContext";

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

export default function LoginForm({ onSuccess }) {
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
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

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const result = await login(loginData.email, loginData.password);
    
    setLoading(false);
    
    if (result.success) {
      onSuccess?.();
      // Optionally redirect to a specific page
      // window.location.href = '/setup'; // or use navigate('/setup')
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
      // Optionally show success message
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
    <Paper elevation={3} sx={{ maxWidth: 400, mx: "auto", mt: 4 }}>
      <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs value={tab} onChange={handleTabChange} aria-label="auth tabs">
          <Tab label="Sign In" />
          <Tab label="Sign Up" />
        </Tabs>
      </Box>

      <TabPanel value={tab} index={0}>
        <form onSubmit={handleLoginSubmit}>
          <Typography variant="h5" sx={{ mb: 3, textAlign: "center" }}>
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
          <Typography variant="h5" sx={{ mb: 3, textAlign: "center" }}>
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
    </Paper>
  );
}