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
  CircularProgress,
  IconButton
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { forgotPassword } from "../../lib/auth";

export default function ForgotPasswordDialog({ open, onClose }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);

    const result = await forgotPassword(email);

    setLoading(false);

    if (result.success) {
      setSuccess(true);
      setEmail("");
    } else {
      setError(result.message);
    }
  };

  const handleClose = () => {
    setEmail("");
    setError("");
    setSuccess(false);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ position: 'relative', pb: 1 }}>
        <Typography variant="h5" component="div">
          Reset Password
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

      <DialogContent>
        {success ? (
          <Box sx={{ py: 2 }}>
            <Alert severity="success" sx={{ mb: 2 }}>
              Password reset link has been sent to your email!
            </Alert>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Please check your email inbox and follow the instructions to reset your password.
            </Typography>
            <Button
              variant="contained"
              fullWidth
              onClick={handleClose}
            >
              Close
            </Button>
          </Box>
        ) : (
          <form onSubmit={handleSubmit}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Enter your email address and we'll send you a link to reset your password.
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              margin="normal"
              required
              disabled={loading}
              autoFocus
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{ mt: 3 }}
              disabled={loading || !email}
            >
              {loading ? <CircularProgress size={24} /> : "Send Reset Link"}
            </Button>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
