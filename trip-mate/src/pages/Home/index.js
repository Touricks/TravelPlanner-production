import { useState } from "react";
import Button from "@mui/material/Button";
import { Link } from "react-router-dom";
import PageContainer from "../../layouts/PageContainer";
import { Typography } from "@mui/material";
import bg from "../../assets/bg.png";

import { useAuth } from "../../auth/AuthContext";
import LoginModal from "../../components/auth/LoginModal";

export default function Home() {
  const { user } = useAuth();
  const [loginModalOpen, setLoginModalOpen] = useState(false);

  const handleCreateTripClick = () => {
    if (user) {
      // User is authenticated, proceed to setup
      return;
    } else {
      // User is not authenticated, show login modal
      setLoginModalOpen(true);
    }
  };

  return (
    <PageContainer
      center
      sx={{
        pt: 20,
        backgroundImage: `url(${bg})`,
        backgroundSize: '100%',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'bottom',
      }}
      maxWidth="false"
    >
      <Typography variant="h2" fontWeight={800} gutterBottom>
        Your journey starts here
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 6 }}>
        sign in now
      </Typography>
      
      {user ? (
        <Button size="large" variant="contained" component={Link} to="/setup">
          Create a Trip
        </Button>
      ) : (
        <Button
          size="large"
          variant="contained"
          onClick={handleCreateTripClick}
        >
          Create a Trip
        </Button>
      )}

      <LoginModal 
        open={loginModalOpen} 
        onClose={() => setLoginModalOpen(false)}
        onSuccess={() => setLoginModalOpen(false)}
      />
    </PageContainer>
  );
}