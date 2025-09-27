# Jarvis Web UI

A beautiful, modern web interface for the Jarvis AI assistant built with Next.js, Radix UI, and shadcn/ui.

## Features

- 🎨 Beautiful, modern design with smooth animations
- ⚡ Built with Next.js 14 and TypeScript
- 🎭 Radix UI components for accessibility
- 🎨 shadcn/ui for consistent styling
- ✨ Framer Motion for smooth animations
- 🌙 Dark mode support
- 📱 Responsive design

## Getting Started

1. Install dependencies:

```bash
npm install
```

2. Run the development server:

```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **Animations**: Framer Motion
- **Icons**: Lucide React

## Project Structure

```
├── app/                 # Next.js app directory
│   ├── globals.css     # Global styles
│   ├── layout.tsx      # Root layout
│   └── page.tsx        # Home page
├── components/         # React components
│   ├── ui/            # shadcn/ui components
│   ├── ai-response.tsx # AI response display
│   ├── input-form.tsx  # Input form component
│   └── hero-section.tsx # Hero section
└── lib/               # Utility functions
    └── utils.ts       # Class name utilities
```
