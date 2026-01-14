// budget options (per-person per-meal rates in cents)
export const budgetOptions = [
  {
    id: "1",
    value: "Any",
    label: "Flexible budget (No limit)",
    icon: "",
    mealRateCents: null,
  },
  {
    id: "2",
    value: "Budget",
    label: "$20 per meal",
    icon: "💰",
    mealRateCents: 2000,
  },
  {
    id: "3",
    value: "Moderate",
    label: "$40 per meal",
    icon: "💰💰",
    mealRateCents: 4000,
  },
  {
    id: "4",
    value: "Upscale",
    label: "$100 per meal",
    icon: "💰💰💰",
    mealRateCents: 10000,
  },
  {
    id: "5",
    value: "Luxury",
    label: "$200 per meal",
    icon: "💰💰💰💰",
    mealRateCents: 20000,
  },
];
// travel style options - mapped 1:1 to backend AttractionCategory enum
export const travelStyles = [
  { id: "CULTURE", label: "Culture", icon: "🏛️" },
  { id: "HISTORICAL", label: "Historical Sites", icon: "🏺" },
  { id: "NATURE", label: "Nature", icon: "🏔️" },
  { id: "ADVENTURE", label: "Adventure", icon: "🧗" },
  { id: "FOOD", label: "Food & Drink", icon: "🍽️" },
  { id: "SHOPPING", label: "Shopping", icon: "🛍️" },
  { id: "NIGHTLIFE", label: "Nightlife", icon: "🌙" },
  { id: "MUSEUM", label: "Museums", icon: "🏛️" },
  { id: "ENTERTAINMENT", label: "Entertainment", icon: "🎭" },
  { id: "SPORTS", label: "Sports", icon: "⚽" },
  { id: "ART", label: "Art", icon: "🎨" },
];

// transportation options - mapped 1:1 to backend TravelMode enum (single-select)
export const transportationOptions = [
  { id: "DRIVING", label: "Rental Car", icon: "🚗" },
  { id: "TRANSIT", label: "Public Transit", icon: "🚇" },
  { id: "WALKING", label: "Walking", icon: "🚶‍♀️" },
  { id: "BICYCLING", label: "Bicycling", icon: "🚴" },
];

// travel pace options - mapped 1:1 to backend TravelPace enum (single-select)
export const travelPaceOptions = [
  { id: "RELAXED", label: "Relaxed (2 POIs/day)", icon: "🌴" },
  { id: "MODERATE", label: "Moderate (4 POIs/day)", icon: "🚶" },
  { id: "PACKED", label: "Packed (5 POIs/day)", icon: "🏃" },
];

// activity intensity options - mapped 1:1 to backend ActivityIntensity enum (single-select)
export const activityIntensityOptions = [
  {
    id: "LIGHT",
    label: "Light & Easy",
    icon: "☕",
    description: "Minimal walking, museums, cafes, scenic views",
  },
  {
    id: "MODERATE",
    label: "Balanced Mix",
    icon: "🚶",
    description: "Walking tours, light activities",
  },
  {
    id: "INTENSE",
    label: "Active & Energetic",
    icon: "🏃",
    description: "Hiking, sports, adventure activities",
  },
];

// dietary options
export const dietaryOptions = [
  { id: "none", label: "None", icon: "✅" },
  { id: "vegetarian", label: "Vegetarian", icon: "🥬" },
  { id: "vegan", label: "Vegan", icon: "🌱" },
  { id: "allergies", label: "Allergies", icon: "⚠️" },
];
