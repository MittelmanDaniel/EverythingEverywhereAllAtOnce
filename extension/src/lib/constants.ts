export const API_URL = "http://localhost:8000";

export const SERVICES = {
  github: {
    name: "GitHub",
    domains: [".github.com", "github.com"],
    icon: "🐙",
    description: "Repos, stars, contributions",
  },
  youtube: {
    name: "YouTube",
    domains: [".youtube.com", "youtube.com", ".google.com"],
    icon: "▶️",
    description: "Playlists, subscriptions, watch history",
  },
  goodreads: {
    name: "Goodreads",
    domains: [".goodreads.com", "goodreads.com"],
    icon: "📚",
    description: "Reading lists, shelves, challenges",
  },
} as const;

export type ServiceKey = keyof typeof SERVICES;
