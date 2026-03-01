import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Everything Everywhere All At Once",
  description: "Discover the paths you didn't take",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0a0a0a] text-gray-200 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
