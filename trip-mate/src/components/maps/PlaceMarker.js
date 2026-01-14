import React, { memo, useMemo, useCallback } from "react";
import { Marker } from "@react-google-maps/api";

/**
 * Generic place marker:
 * - id: Unique key (used for memo comparison)
 * - position: { lat, lng } (LatLngLiteral)
 * - place: Original place object (returned on click)
 * - iconUrl: Marker icon URL
 * - size: Icon size (square), default 32
 * - labelText: Label text (automatically converted to a non-empty string)
 * - onSelect(place): Callback triggered on click
 * - zIndex: Optional
 */
function PlaceMarkerImpl({
  id,
  position,
  place,
  iconUrl,
  size = 32,
  labelText,
  onSelect,
  zIndex,
  isSelectedAttraction
}) {
  const label = useMemo(() => {
    const text = String(labelText ?? " ");
    return {
      text, // Value must not be an empty string
      color: "white",
      fontSize: isSelectedAttraction ? "22px" : "14px",
      fontWeight: "bold",
    };
  }, [labelText, isSelectedAttraction]);

  const icon = useMemo(() => {
    const g = window.google;
    if (!g?.maps) return undefined; // Bypass execution until the Map instance is ready
    const actualSize = isSelectedAttraction ? size * 1.5 : size;
    return {
      url: iconUrl,
      scaledSize: new g.maps.Size(actualSize, actualSize),
      // Align the label to the upper middle of the icon; can be adjusted if required
      labelOrigin: new g.maps.Point(actualSize / 2, actualSize * 0.375),
    };
  }, [iconUrl, size, isSelectedAttraction]);

  const handleClick = useCallback(() => {
    onSelect?.(place);
  }, [onSelect, place]);

  return (
    <Marker
      position={position}
      onClick={handleClick}
      label={label}
      icon={icon}
      zIndex={zIndex}
    />
  );
}

// Trigger updates only on changes to essential fields
export default memo(PlaceMarkerImpl, (prev, next) =>
  prev.id === next.id &&
  prev.iconUrl === next.iconUrl &&
  prev.size === next.size &&
  (prev.labelText ?? " ") === (next.labelText ?? " ") &&
  prev.position?.lat === next.position?.lat &&
  prev.position?.lng === next.position?.lng &&
  prev.place === next.place &&
  prev.onSelect === next.onSelect &&
  prev.zIndex === next.zIndex &&
  prev.isSelectedAttraction === next.isSelectedAttraction
);
