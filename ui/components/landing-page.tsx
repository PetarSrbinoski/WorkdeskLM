// FILE: components/landing-page.tsx
'use client'

import { Button } from '@/components/ui/button'
import { BookOpen, Moon, Sun } from 'lucide-react'
import LightRays from '@/components/light-rays'

interface LandingPageProps {
  onStart: () => void
  darkMode: boolean
  onToggleDarkMode: () => void
}

export function LandingPage({ onStart, darkMode, onToggleDarkMode }: LandingPageProps) {
  return (
    <div className="min-h-screen relative overflow-hidden bg-background">
      {/* Light Rays Background - adapts to dark/light mode */}
      <div className="absolute inset-0">
        <LightRays
          raysOrigin="top-center"
          raysColor={darkMode ? '#dc2626' : '#ffffff'}
          raysSpeed={0.8}
          lightSpread={1.2}
          rayLength={2}
          pulsating={false}
          fadeDistance={1.2}
          saturation={0.9}
          followMouse={false}
          mouseInfluence={0}
          noiseAmount={0}
          distortion={0.0}
          className="w-full h-full"
        />
      </div>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6">
        {/* Logo */}
        <div
          className="size-20 sm:size-24 rounded-2xl bg-crimson flex items-center justify-center mb-10 shadow-lg"
          style={{ boxShadow: '0 10px 40px oklch(0.5 0.2 25 / 0.4)' }}
        >
          <BookOpen className="size-10 sm:size-12 text-white" />
        </div>

        {/* Title */}
        <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold tracking-tight text-center mb-6">
          <span className="text-foreground">Workdesk</span>
          <span className="text-crimson">LM</span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl md:text-2xl text-muted-foreground text-center max-w-2xl mb-2">
          Local-first AI assistant for your documents.
        </p>
        <p className="text-lg sm:text-xl md:text-2xl font-medium text-foreground text-center mb-10">
          100% private. Always available.
        </p>

        {/* Button */}
        <Button 
          size="lg" 
          onClick={onStart}
          className="bg-crimson hover:bg-crimson/90 text-white px-10 h-14 text-lg rounded-full shadow-lg cursor-pointer"
          style={{ boxShadow: '0 6px 28px oklch(0.5 0.2 25 / 0.5)' }}
        >
          Start Chat
        </Button>
      </div>
    </div>
  )
}