import Button from "@mui/material/Button";

export default function SmallButton(props) {
  return (
    <Button
      variant="outlined"
      sx={{
        fontSize: "0.75rem",
        padding: "6px 8px",
        minWidth: "auto",
        lineHeight: 1.2,
      }}
      {...props}
    />
  );
}
