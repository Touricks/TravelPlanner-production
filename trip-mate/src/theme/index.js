import { createTheme } from '@mui/material/styles';

const blackButtonTheme = createTheme({
  palette: {
    primary: {
      main: '#000000',
      light: '#333333',
      dark: '#000000',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#E0E0E0',
      light: '#F5F5F5',
      dark: '#A0A0A0',
      contrastText: '#000000',
    },
    error: {
      main: '#f44336',
    },
    warning: {
      main: '#ff9800',
    },
    info: {
      main: '#2196f3',
    },
    success: {
      main: '#4caf50',
    },
    text: {
      primary: '#333333',
      secondary: '#666666',
    },
    background: {
      default: '#FFFFFF',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '3rem',
      fontWeight: 700,
      color: '#333333',
    },
    h2: {
      fontSize: '2.5rem',
      fontWeight: 600,
      color: '#333333',
    },
    h3: {
      fontSize: '2rem',
      fontWeight: 600,
      color: '#333333',
    },
    h4: {
      fontSize: '1.75rem',
      fontWeight: 500,
      color: '#666666',
    },
    h5: {
      fontSize: '1.5rem',
      fontWeight: 500,
      color: '#666666',
    },
    h6: {
      fontSize: '1.25rem',
      fontWeight: 500,
      color: '#666666',
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
      color: '#333333',
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.4,
      color: '#666666',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      color: '#FFFFFF',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 20px',
        },
        containedPrimary: {
          backgroundColor: '#000000',
          '&:hover': {
            backgroundColor: '#333333',
          },
        },
        outlinedPrimary: {
          borderColor: '#000000',
          color: '#000000', 
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
            borderColor: '#333333',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          color: '#333333',
          boxShadow: 'none',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.05)',
          backgroundColor: '#FFFFFF',
        },
      },
    },
    MuiLink: {
      styleOverrides: {
        root: {
          color: '#000000',
          '&:hover': {
            color: '#333333',
          },
        },
      },
    },
  },
});

export default blackButtonTheme;