"use client";

import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6">
      <div className="max-w-2xl text-center">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          Everything Everywhere
          <br />
          All At Once
        </h1>
        <p className="text-lg text-gray-400 mb-2">
          Your digital life is full of paths not taken.
        </p>
        <p className="text-gray-500 mb-10 max-w-md mx-auto">
          Abandoned projects. Unfinished books. Forgotten interests.
          Discover the roads you didn&apos;t travel — and maybe find your way back.
        </p>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => router.push("/signup")}
            className="px-8 py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-medium transition-colors"
          >
            Get Started
          </button>
          <button
            onClick={() => router.push("/login")}
            className="px-8 py-3 border border-gray-700 hover:border-gray-500 text-gray-300 rounded-lg font-medium transition-colors"
          >
            Log In
          </button>
        </div>
      </div>
    </main>
  );
}
