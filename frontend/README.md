# FISHER Dashboard

FISHER is a responsive operations command center for CCTV monitoring, AI detection review, security alerts, operational statistics, reports, and user access management.

It is currently a front-end MVP built for product demonstrations, stakeholder walkthroughs, and interaction design validation. The interface uses realistic mock data and local UI state; it does not yet connect to a production API or database.

## Product Experience

The dashboard is organized around fast operational scanning:

- **Dashboard:** high-level camera, availability, and alert metrics
- **Live CCTV:** camera availability cards with online/offline states and expandable feeds
- **Alert Center:** unread, new, acknowledged, critical, and resolved alert workflows
- **Detection Results:** filterable detection review with severity and status actions
- **Statistics:** severity distribution, totals, percentages, and detection detail views
- **Reports:** generated report summaries with status and detail views
- **User Management:** user creation, role management, status controls, and detail views

The sidebar follows the operational order `Dashboard`, `Live CCTV`, `Alert Center`, `Detection Results`, `Statistics`, `Reports`, and `User Management`. Navigation uses URL hash targets, so sections remain linkable and browser navigation stays predictable.

## Alert Operations

Alert Center is the most interactive workflow in the prototype. Operators can:

- filter alerts by all, new, acknowledged, or critical status
- mark individual alerts or all alerts as read
- acknowledge and resolve alerts
- open a detailed investigation modal
- select SMS and Telegram notification channels
- track notification states: ready, sending, sent, or failed

The notification action currently calls `/api/alerts/:id/notify`. A backend endpoint is required for delivery to work in a deployed environment; the UI gracefully represents request failures.

## Interface System

- Responsive fixed sidebar with independent navigation scrolling
- Desktop and mobile layouts for operational use
- Persistent light/dark theme preference through `localStorage`
- Ethiopian-inspired green, yellow, and red status accents
- Accessible focus states and semantic buttons/links
- Consistent card surfaces, status badges, empty states, and detail modals
- Compact mobile typography designed for narrow dashboard views

## Technology

- React 19
- TypeScript
- Vite
- Custom CSS design system
- Mock service layer for local dashboard data
- Oxlint for static analysis

## Project Structure

```text
fisher-dashboard/
├── public/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── alerts/       Alert Center and investigation workflow
│   │   ├── cctv/         Camera feed cards
│   │   ├── common/       Shared icons and UI primitives
│   │   ├── detections/   Detection review tables and details
│   │   ├── layout/       App shell, sidebar, and top bar
│   │   ├── reports/      Report generation and details
│   │   ├── statistics/   Metrics and severity analysis
│   │   └── users/        User and access management
│   ├── data/             Mock cameras, detections, alerts, users, reports
│   ├── pages/            Dashboard composition and section wiring
│   ├── services/         Data access facade for the mock layer
│   ├── types/            Shared TypeScript domain models
│   ├── App.tsx
│   ├── App.css
│   ├── index.css         Global layout, themes, responsive design
│   └── main.tsx
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Getting Started

### Requirements

- Node.js 18 or newer
- npm

### Install

```bash
npm install
```

### Start development

```bash
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

### Production build

```bash
npm run build
```

### Preview the production build

```bash
npm run preview
```

### Lint

```bash
npm run lint
```

### Unit and component tests

```bash
npm test
```

Run the unit suite in watch mode while developing:

```bash
npm run test:watch
```

### Browser smoke tests

Install the local Chromium runtime once:

```bash
npx playwright install chromium
```

Then run the desktop and mobile browser checks:

```bash
npm run test:e2e
```

The Playwright suite checks the desktop and mobile dashboard shell, theme switching, and sidebar visibility.

## Data Boundary

Mock domain data lives in `src/data/dashboardData.ts` and is exposed through `src/services/dashboardService.ts`. Shared contracts live in `src/types/dashboard.ts`.

The current prototype intentionally keeps the data layer lightweight. A production implementation can replace the service functions with API calls while preserving the component contracts and dashboard workflows.

## Quality Notes

The project is optimized for:

- product and stakeholder demos
- responsive UI validation
- operational workflow prototyping
- future API and authentication integration

Before production deployment, connect the notification endpoint, add authentication and role-based access control, replace mock data with a resilient data source, and add automated component and browser tests.

The current validation path is:

```bash
npm run lint
npm test
npm run test:e2e
npm run build
```

The repository also includes a GitHub Actions workflow at `.github/workflows/ci.yml` that installs the browser runtime and runs the complete validation path on pushes and pull requests.

## License

This project is intended for educational, demonstration, and product-design use.
