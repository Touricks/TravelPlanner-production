import { useJsApiLoader } from "@react-google-maps/api";

const LIBRARIES = ["places"];

export default function MapsProvider({ children }) {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.REACT_APP_MAPS_BROWSER_KEY,
    libraries: LIBRARIES,
  });

  if (loadError) return <div>Failed to load Google Maps</div>;

  if (!isLoaded) return <div>Loading map services…</div>;

  return children;
}