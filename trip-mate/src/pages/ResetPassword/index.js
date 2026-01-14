import { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  Paper,
  CircularProgress,
  Container
} from "@mui/material";
import { resetPassword } from "../../lib/auth";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const [formData, setFormData] = useState({
    newPassword: "",
    confirmPassword: ""
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [validationError, setValidationError] = useState("");

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing reset token. Please request a new password reset link.");
    }
  }, [token]);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => {
        navigate("/");
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [success, navigate]);

  const validatePassword = (password) => {
    if (password.length < 8) {
      return "Password must be at least 8 characters long";
    }
    return "";
  };

  const handleChange = (field) => (e) => {
    const value = e.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    setValidationError("");
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setValidationError("");

    // Validate password
    const passwordError = validatePassword(formData.newPassword);
    if (passwordError) {
      setValidationError(passwordError);
      return;
    }

    // Check passwords match
    if (formData.newPassword !== formData.confirmPassword) {
      setValidationError("Passwords do not match");
      return;
    }

    if (!token) {
      setError("Invalid reset token");
      return;
    }

    setLoading(true);

    const result = await resetPassword(token, formData.newPassword);

    setLoading(false);

    if (result.success) {
      setSuccess(true);
      setFormData({ newPassword: "", confirmPassword: "" });
    } else {
      setError(result.message);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ mb: 3 }}>
            Reset Your Password
          </Typography>

          {success ? (
            <Box sx={{ textAlign: "center" }}>
              <Alert severity="success" sx={{ mb: 3 }}>
                Your password has been reset successfully!
              </Alert>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Redirecting to home page in 3 seconds...
              </Typography>
              <Button
                variant="contained"
                component={Link}
                to="/"
                fullWidth
              >
                Go to Home
              </Button>
            </Box>
          ) : (
            <form onSubmit={handleSubmit}>
              {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
              {validationError && <Alert severity="warning" sx={{ mb: 2 }}>{validationError}</Alert>}

              {!token && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  Invalid or missing reset token. Please request a new password reset.
                </Alert>
              )}

              <TextField
                fullWidth
                label="New Password"
                type="password"
                value={formData.newPassword}
                onChange={handleChange("newPassword")}
                margin="normal"
                required
                disabled={loading || !token}
                helperText="Password must be at least 8 characters long"
              />

              <TextField
                fullWidth
                label="Confirm Password"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange("confirmPassword")}
                margin="normal"
                required
                disabled={loading || !token}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading || !token || !formData.newPassword || !formData.confirmPassword}
              >
                {loading ? <CircularProgress size={24} /> : "Reset Password"}
              </Button>

              <Box sx={{ textAlign: "center", mt: 2 }}>
                <Link to="/" style={{ textDecoration: "none" }}>
                  <Typography variant="body2" color="primary">
                    Back to Home
                  </Typography>
                </Link>
              </Box>
            </form>
          )}
        </Paper>
      </Box>
    </Container>
  );
}
