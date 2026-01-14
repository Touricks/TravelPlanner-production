import axios from "axios";
import { getAuthToken, removeAuthToken, isTokenExpired } from "../lib/auth";
import { budgetOptions } from "../components/travel-setup/travelSetupOptions";

const base = process.env.REACT_APP_API_BASE || "/api";

const api = axios.create({
  baseURL: base,
});

// Request interceptor to add JWT token to headers
api.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    console.log('Request interceptor - URL:', config.url);
    console.log('Request interceptor - Token available:', !!token);
    
    if (token && !isTokenExpired(token)) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Request interceptor - Added Authorization header');
    } else {
      console.log('Request interceptor - No valid token, skipping Authorization header');
      if (token) {
        console.log('Request interceptor - Token expired');
      }
    }
    console.log('Request interceptor - Headers:', config.headers);
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    console.log('Response interceptor - Error details:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
      url: error.config?.url,
      method: error.config?.method
    });
    
    if (error.response && error.response.status === 401) {
      // Token is invalid or expired
      removeAuthToken();
      // Redirect to home page for re-authentication
      window.location.href = "/";
    } else if (error.response && error.response.status === 403) {
      console.error('403 Forbidden - User may not have permission or backend authorization issue');
    }
    return Promise.reject(error);
  }
);

export async function getAttractions(payload) {
  const res = await api.post(`${base}/attractions_mock`, payload);
  return res;
}

export async function getTripPlan(payload) {
  // const res = await api.post(`${base}/itinerary`, payload);
  const res = await fetch("/mock/itinerary.json").then((r) => r.json());
  return res;
}

export async function createTrip(payload) {
  try {
    // Debug authentication state before API call
    const token = getAuthToken();
    console.log('createTrip - Auth token available:', !!token);
    console.log('createTrip - Token expired:', token ? isTokenExpired(token) : 'no token');
    if (token) {
      const decoded = token.split('.')[1];
      try {
        const tokenPayload = JSON.parse(atob(decoded.replace(/-/g, '+').replace(/_/g, '/')));
        console.log('createTrip - Token payload:', tokenPayload);
      } catch (e) {
        console.log('createTrip - Could not decode token');
      }
    }
    
    // Calculate budget: per-person per-meal rate × travelers × days × meals per day
    const numberOfTravelers = payload.travelers.adults + payload.travelers.children + payload.travelers.infants + (payload.travelers.elderly || 0);
    const days = Math.max(1, Math.ceil((new Date(payload.endDate) - new Date(payload.startDate)) / (1000 * 60 * 60 * 24)));
    const mealsPerDay = 2; // Lunch and dinner (breakfast included in hotel)

    const budgetOption = budgetOptions.find(opt => opt.id === payload.budget);
    const mealRateCents = budgetOption?.mealRateCents;
    const budgetLimitCents = mealRateCents ? mealRateCents * numberOfTravelers * days * mealsPerDay : null;

    console.log('Budget calculation:', {
      budgetTier: payload.budget,
      mealRateCents,
      mealsPerDay,
      numberOfTravelers,
      days,
      totalBudgetCents: budgetLimitCents,
      totalBudgetUSD: budgetLimitCents ? `$${(budgetLimitCents / 100).toFixed(2)}` : 'No limit'
    });

    // Debug: Log original preferences from form
    console.log('🔍 DEBUG - Original form preferences:', {
      travelPace: payload.preferences.travelPace,
      activityIntensity: payload.preferences.activityIntensity,
      transportation: payload.preferences.transportation,
      fullPreferences: payload.preferences
    });

    // Transform frontend payload to match backend CreateItineraryRequest model
    const backendPayload = {
      destinationCity: payload.destination,
      startDate: `${payload.startDate}T07:00:00+02:00`,
      endDate: `${payload.endDate}T22:00:00+02:00`,
      travelMode: payload.preferences.transportation || null, // DRIVING/TRANSIT/WALKING/BICYCLING
      budgetLimitCents: budgetLimitCents,
      travelPace: payload.preferences.travelPace || "MODERATE", // Use form value with fallback
      activityIntensity: payload.preferences.activityIntensity || "MODERATE", // Use form value with fallback
      preferredCategories: payload.preferences.travelStyle || [], // Array of AttractionCategory enums
      numberOfTravelers: numberOfTravelers,
      hasChildren: payload.travelers.children > 0,
      hasElderly: (payload.travelers.elderly || 0) > 0,
      preferPopularAttractions: false, // Not collected in UI
      additionalPreferences: payload.preferences.mustSeePlaces || null
    };
    
    console.log('🚀 createTrip - Backend payload (matching CreateItineraryRequest):', backendPayload);
    console.log('🔍 DEBUG - travelPace:', backendPayload.travelPace, 'activityIntensity:', backendPayload.activityIntensity);
    
    // Use the correct endpoint from OpenAPI spec with explicit Content-Type
    const res = await api.post('/itineraries', backendPayload, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    console.log('createTrip - Itinerary created successfully:', res.data);
    
    // Transform backend response to match frontend expectations
    return {
      success: true,
      data: {
        id: res.data.itineraryId,
        destination: res.data.destinationCity,
        createdAt: new Date().toISOString(),
        ...res.data
      }
    };
  } catch (error) {
    console.error('createTrip - Detailed error:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
      url: error.config?.url,
      requestHeaders: error.config?.headers,
      requestData: error.config?.data
    });
    throw error; // Re-throw to maintain error handling flow
  }

  // Mock implementation for development
  // return new Promise((resolve) => {
  //   setTimeout(() => {
  //     resolve({
  //       success: true,
  //       data: {
  //         id: "1021",
  //         destination: payload?.destination || "San Francisco",
  //         createdAt: new Date().toISOString(),
  //       },
  //     });
  //   }, 10000);
  // });
}

export async function getTrip({ id }) {
  // Real backend call - JWT automatically added by interceptor
  const res = await api.get(`/trips/${id}`);
  return res.data;

  // Mock implementation for development
  // return Promise.resolve({
  //   success: true,
  //   data: {
  //     destination: "San Francisco",
  //     duration: 8,
  //     interests: ["ChIJmRyMs_mAhYARpViaf6JEWNE"],
  //   },
  // });
}

export async function getTripAttractions({ id }) {
  // Real backend call - JWT automatically added by interceptor
  const res = await api.get(`/trips/${id}/attractions`);
  return res.data;

  // Mock implementation for development
  // const res = await fetch("/mock/attractions.json").then((r) => r.json());
  // return res;
}

export async function getTripProcess({ id }) {
  // Real backend call - JWT automatically added by interceptor
  const res = await api.get(`/trips/${id}/progress`);
  return res.data;

  // Mock implementation for development
  // const trip = {
  //   id,
  //   status: Math.random() > 0.7 ? "ready" : "processing",
  // };
  // const progress = trip.status === "ready" ? 100 : Math.floor(Math.random() * 100);
  // return Promise.resolve({
  //   success: true,
  //   data: {
  //     status: trip.status,
  //     progress,
  //   },
  // });
}

export async function getUserItineraries(page = 0, size = 20) {
  // Real backend call - JWT automatically added by interceptor
  const res = await api.get('/itineraries', {
    params: { page, size }
  });
  return res.data;

  // Fallback to mock data for development
  // return Promise.resolve({
  //   items: [
  //     {
  //       id: "123",
  //       destinationCity: "San Francisco",
  //       startDate: "2024-12-15T10:00:00Z",
  //       endDate: "2024-12-20T18:00:00Z",
  //       travelMode: "DRIVING",
  //       travelPace: "MODERATE",
  //     },
  //     {
  //       id: "456",
  //       destinationCity: "Tokyo",
  //       startDate: "2025-01-10T08:00:00Z",
  //       endDate: "2025-01-17T20:00:00Z",
  //       travelMode: "TRANSIT",
  //       travelPace: "PACKED",
  //     },
  //     {
  //       id: "789",
  //       destinationCity: "Paris",
  //       startDate: "2025-03-05T12:00:00Z",
  //       endDate: "2025-03-12T16:00:00Z",
  //       travelMode: "WALKING",
  //       travelPace: "RELAXED",
  //     },
  //   ],
  //   page: {
  //     page: 0,
  //     size: 20,
  //     totalElements: 3,
  //     totalPages: 1,
  //   },
  // });
}

export async function getItineraryById(itineraryId) {
  try {
    // Real backend call - JWT automatically added by interceptor
    const res = await api.get(`/itineraries/${itineraryId}`);
    return res.data;
  } catch (error) {
    console.error('Failed to get itinerary:', error.message);
    throw error;
  }
}

export async function getItineraryRecommendations(itineraryId, page = 0, size = 20) {
  try {
    // Real backend call - JWT automatically added by interceptor
    const res = await api.get(`/itineraries/${itineraryId}/recommendations`, {
      params: { page, size }
    });
    return res.data;
  } catch (error) {
    console.error('Failed to get recommendations:', error.message);
    throw error;
  }
}

export async function getItineraryImage(itineraryId) {
  try {
    const attractions = await getTripAttractions({ id: itineraryId });
    return attractions?.data?.[0]?.imageUrl || null;
  } catch (error) {
    console.warn(`Failed to fetch image for itinerary ${itineraryId}:`, error);
    return null;
  }
}

export async function getItineraryFirstPlaceImage(itineraryId) {
  try {
    // Get the first recommendation from the itinerary
    const recommendations = await getItineraryRecommendations(itineraryId, 0, 1);
    const firstPlace = recommendations?.items?.[0];
    
    if (!firstPlace) {
      return null;
    }

    // Return the place data for Google Places photo fetching
    return {
      name: firstPlace.name,
      address: firstPlace.address,
      location: firstPlace.location
    };
  } catch (error) {
    console.warn(`Failed to fetch first place for itinerary ${itineraryId}:`, error);
    return null;
  }
}

export async function addInterest(itineraryId, placeId, pinned = false) {
  try {
    const res = await api.post(`/itineraries/${itineraryId}/interests`, {
      placeId,
      pinned
    });
    return res.data;
  } catch (error) {
    console.error('Failed to add interest:', error);
    throw error;
  }
}

export async function planItinerary(itineraryId, planRequest = {}) {
  try {
    const res = await api.post(`/itineraries/${itineraryId}/plan`, planRequest);
    return res.data;
  } catch (error) {
    console.error('Failed to plan itinerary:', error);
    throw error;
  }
}

export async function getPlanHistory(itineraryId) {
  try {
    // Real backend call - JWT automatically added by interceptor
    const res = await api.get(`/itineraries/${itineraryId}/plans`);
    return res.data;
  } catch (error) {
    console.error('Failed to fetch plan history:', error);
    throw error;
  }
}

export async function getActivePlan(itineraryId) {
  try {
    // Real backend call - JWT automatically added by interceptor
    const res = await api.get(`/itineraries/${itineraryId}/plan`);
    return res.data;
  } catch (error) {
    console.error('Failed to fetch active plan:', error);
    throw error;
  }
}

export async function updateInterest(itineraryId, placeId, pinned) {
  try {
    // Debug token
    const token = getAuthToken();
    console.log('Auth token available:', !!token);
    console.log('Token expired:', token ? isTokenExpired(token) : 'no token');
    
    console.log('API call updateInterest with:', { itineraryId, placeId, pinned });
    
    const res = await api.post(`/itineraries/${itineraryId}/interests`, {
      placeId,
      pinned
    });
    return res.data;
  } catch (error) {
    console.error('API Error details:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
      config: {
        url: error.config?.url,
        method: error.config?.method,
        headers: error.config?.headers
      }
    });
    throw error;
  }
}

/**
 * Delete a place from an itinerary (hard delete)
 */
export async function deletePlace(itineraryId, placeId) {
  try {
    console.log('API call deletePlace with:', { itineraryId, placeId });
    const res = await api.delete(`/itineraries/${itineraryId}/places/${placeId}`);
    return res.data;
  } catch (error) {
    console.error('Delete place error:', error.response?.data || error.message);
    throw error;
  }
}

/**
 * Add a new place to an itinerary
 */
export async function addPlace(itineraryId, placeData) {
  try {
    console.log('API call addPlace with:', { itineraryId, placeData });
    const res = await api.post(`/itineraries/${itineraryId}/places`, placeData);
    return res.data;
  } catch (error) {
    console.error('Add place error:', error.response?.data || error.message);
    throw error;
  }
}
