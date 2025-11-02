# AI Trading Dashboard - Frontend

Modern, responsive web dashboard for the AI Trading Agent built with Next.js, TypeScript, and TailwindCSS.

## Features

- 📊 Real-time portfolio monitoring
- 🤖 AI signal visualization with confidence scores
- 📈 Live position tracking with advanced table features (sorting, filtering)
- 📊 Comprehensive performance analytics with charts
- 🔄 WebSocket integration for real-time updates
- 📱 Responsive design (mobile-friendly)
- ⚡ Fast, optimized performance with SWR
- 🎨 Hybrid UI approach (Shadcn + Ant Design)

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** TailwindCSS
- **UI Libraries:** Shadcn UI + Ant Design (hybrid approach)
- **Data Fetching:** SWR (stale-while-revalidate)
- **Charts:** @ant-design/charts
- **API Client:** Axios
- **Icons:** Lucide React + @ant-design/icons
- **Animations:** Framer Motion

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

## Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
frontend_web/
├── src/
│   ├── app/              # Next.js app directory
│   │   ├── page.tsx      # Main dashboard
│   │   ├── layout.tsx    # Root layout
│   │   └── globals.css   # Global styles
│   └── services/
│       └── api.ts        # API client
├── public/               # Static assets
├── package.json
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

## API Integration

The dashboard connects to the FastAPI backend at `http://localhost:8000` by default.

### Endpoints Used

- `GET /api/v1/health` - Health check
- `GET /api/v1/predict` - Get AI predictions
- `GET /api/v1/portfolio/status` - Portfolio status
- `GET /api/v1/positions` - Active positions
- `POST /api/v1/trade` - Execute trade
- `WS /ws` - WebSocket for real-time updates

## Docker Deployment

```bash
# Build image
docker build -t trading-frontend .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api:8000 trading-frontend
```

## Features to Add (Future)

- [ ] Advanced charting with TradingView
- [ ] Analytics page with detailed metrics
- [ ] Backtesting interface
- [ ] Model performance monitoring
- [ ] Risk dashboard
- [ ] Trade history with filtering
- [ ] Export functionality (CSV/PDF)
- [ ] Dark mode toggle
- [ ] User authentication
- [ ] Mobile app integration

## Development

```bash
# Run linter
npm run lint

# Type check
npx tsc --noEmit
```

## License

MIT


