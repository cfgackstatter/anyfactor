import { createTheme } from '@mui/material/styles';

const ink = '#0B1F2A';
const muted = '#5B6B75';
const line = '#C5D0DA';
const paper = '#FFFFFF';
const wash = '#E8EDF2';
const accent = '#0E5C4A';
const accentHover = '#0A4638';

const theme = createTheme({
  spacing: 4,
  shape: { borderRadius: 2 },
  typography: {
    fontFamily: '"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif',
    fontSize: 13,
    h1: { fontSize: '1.25rem', fontWeight: 600, letterSpacing: '-0.02em', color: ink },
    h2: { fontSize: '0.95rem', fontWeight: 600, letterSpacing: '-0.01em', color: ink },
    h6: { fontSize: '0.85rem', fontWeight: 600, color: ink },
    body1: { fontSize: '0.8125rem', color: ink },
    body2: { fontSize: '0.75rem', color: muted },
    caption: { fontSize: '0.6875rem', color: muted, letterSpacing: '0.02em' },
    button: { textTransform: 'none', fontWeight: 600, fontSize: '0.8125rem' },
  },
  palette: {
    mode: 'light',
    primary: { main: accent, dark: accentHover, contrastText: '#fff' },
    secondary: { main: ink },
    background: { default: wash, paper },
    text: { primary: ink, secondary: muted },
    divider: line,
    success: { main: '#1B7F5A' },
    error: { main: '#B42318' },
    warning: { main: '#9A6B00' },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: wash,
          backgroundImage:
            'linear-gradient(rgba(11,31,42,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(11,31,42,0.035) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        },
        '*, *::before, *::after': { boxSizing: 'border-box' },
      },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0, color: 'transparent' },
      styleOverrides: {
        root: {
          backgroundColor: paper,
          borderBottom: `1px solid ${line}`,
          color: ink,
        },
      },
    },
    MuiToolbar: {
      styleOverrides: {
        root: {
          minHeight: '44px !important',
          paddingLeft: '16px !important',
          paddingRight: '16px !important',
        },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: `1px solid ${line}`,
          boxShadow: 'none',
        },
      },
    },
    MuiButton: {
      defaultProps: { size: 'small', disableElevation: true },
      styleOverrides: {
        root: {
          borderRadius: 2,
          minHeight: 32,
          paddingInline: 14,
        },
        containedPrimary: {
          boxShadow: 'none',
          '&:hover': { boxShadow: 'none', backgroundColor: accentHover },
        },
      },
    },
    MuiTextField: {
      defaultProps: { size: 'small', variant: 'outlined' },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: paper,
          '& .MuiOutlinedInput-notchedOutline': { borderColor: line },
          '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: muted },
        },
        input: {
          fontSize: '0.8125rem',
          fontFamily: '"IBM Plex Sans", sans-serif',
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: { fontSize: '0.8125rem' },
      },
    },
    MuiChip: {
      defaultProps: { size: 'small' },
      styleOverrides: {
        root: {
          height: 22,
          borderRadius: 2,
          fontSize: '0.6875rem',
          fontFamily: '"IBM Plex Mono", monospace',
          fontWeight: 500,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          fontSize: '0.75rem',
          padding: '6px 10px',
          borderColor: line,
        },
        head: {
          fontWeight: 600,
          color: muted,
          backgroundColor: '#F3F6F8',
          fontSize: '0.6875rem',
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          whiteSpace: 'nowrap',
        },
        body: {
          fontFamily: '"IBM Plex Mono", monospace',
          fontVariantNumeric: 'tabular-nums',
        },
      },
    },
    MuiLink: {
      styleOverrides: {
        root: {
          color: accent,
          textDecorationColor: 'rgba(14,92,74,0.35)',
          fontSize: '0.75rem',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 2, py: 0.25, fontSize: '0.75rem' },
      },
    },
  },
});

export default theme;
