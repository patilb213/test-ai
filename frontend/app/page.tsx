"use client";

import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Play,
  ShieldCheck,
  Sparkles,
  TestTube2,
} from "lucide-react";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#07090d] text-white">
      {/* Navigation */}
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5">
            <TestTube2 size={21} />
          </div>

          <span className="text-xl font-semibold">
            Test AI
          </span>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="rounded-lg px-4 py-2 text-sm text-gray-300 hover:bg-white/5"
          >
            Login
          </Link>

          <Link
            href="/signup"
            className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-black"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="mx-auto max-w-7xl px-6 pb-24 pt-20">
        <div className="mx-auto max-w-4xl text-center">

          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-purple-300">
            <Sparkles size={15} />
            AI-Powered Web Testing
          </div>

          <h1 className="text-5xl font-bold tracking-tight md:text-7xl">
            Test smarter.
            <br />

            <span className="text-purple-400">
              Ship faster.
            </span>
          </h1>

          <p className="mx-auto mt-7 max-w-2xl text-lg leading-8 text-gray-400">
            Record browser workflows, execute reusable tests,
            verify results and intelligently recover from UI
            changes with Test AI.
          </p>

          {/* Buttons */}
          <div className="mt-9 flex justify-center gap-4">

            <Link
              href="/signup"
              className="flex items-center gap-2 rounded-xl bg-purple-500 px-6 py-3 font-semibold text-white hover:bg-purple-400"
            >
              Start Testing
              <ArrowRight size={18} />
            </Link>

            <Link
              href="/login"
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3 font-semibold text-gray-200 hover:bg-white/10"
            >
              <Play size={17} />
              Demo
            </Link>

          </div>
        </div>

        {/* Features */}
        <div className="mt-20 grid gap-5 md:grid-cols-3">

          <Feature
            icon={<TestTube2 size={22} />}
            title="Scriptless Recording"
            text="Capture clicks, inputs, navigation and other browser actions."
          />

          <Feature
            icon={<ShieldCheck size={22} />}
            title="Smart Verification"
            text="Verify URLs, visible elements and expected text."
          />

          <Feature
            icon={<Sparkles size={22} />}
            title="Self-Healing"
            text="Find suitable replacement elements when UI locators change."
          />

        </div>
      </section>
    </main>
  );
}

function Feature({
  icon,
  title,
  text,
}: {
  icon: React.ReactNode;
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">

      <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400">
        {icon}
      </div>

      <h2 className="text-lg font-semibold">
        {title}
      </h2>

      <p className="mt-3 text-sm leading-6 text-gray-400">
        {text}
      </p>

      <div className="mt-5 flex items-center gap-2 text-xs text-green-400">
        <CheckCircle2 size={14} />
        Included in Test AI
      </div>

    </div>
  );
}