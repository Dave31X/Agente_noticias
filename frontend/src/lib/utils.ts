import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function shortTitle(text: string) {
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > 46 ? `${clean.slice(0, 46)}…` : clean || "Nueva conversación";
}
