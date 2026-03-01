export const API_URL = "http://localhost:8000";

export const SERVICES = {
  google: {
    name: "Google",
    domains: [".google.com", "google.com"],
    icon: "\uD83D\uDD0D",
    description: "Drive, Docs, Gmail",
  },
} as const;

export type ServiceKey = keyof typeof SERVICES;
