# Video Translator Frontend

A Next.js application for uploading and translating videos with real-time progress updates using Server-Sent Events (SSE).

## Features

- Upload video files
- Select target language for translation
- Real-time progress tracking via SSE
- Modern UI built with shadcn/ui components
- TypeScript for type safety

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python backend running on `http://127.0.0.1:8000`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

Create a `.env.local` file (optional):

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Usage

1. Select a video file using the file input
2. Choose your target language from the dropdown
3. Click "Start Processing" to begin translation
4. Watch the real-time progress as the video is processed
5. Download the translated video when complete

## Project Structure

- `app/page.tsx` - Main upload page component
- `lib/api.ts` - API client with SSE support
- `components/ui/` - shadcn/ui components
