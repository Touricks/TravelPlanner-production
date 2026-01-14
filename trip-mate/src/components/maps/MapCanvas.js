import { GoogleMap } from "@react-google-maps/api";
const DEFAULT_CENTER = { lat: 37.7749, lng: -122.4194 };

export default function MapCanvas({ onLoad, children, center = DEFAULT_CENTER }) {
  return (
    <GoogleMap
      onLoad={(map) => { map.setOptions({ clickableIcons: false }); onLoad(map); }}
      mapContainerStyle={{
        width: "100%",
        height: "100%"
      }}
      center={center}
      zoom={12}
    >
      {children}
    </GoogleMap>
  );
}
