# Baroda Fry Centre

Mobile-first React storefront and staff kitchen dashboard, backed by a modular Django application. Inspired by the separate Django configuration/store structure of [WrappDelights](https://github.com/himanshunexus/wrapp_delight).

## Run locally

Requires Python 3.11+ and Node.js 20.19+. Run commands from the repository root unless indicated.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
python backend/manage.py migrate
python backend/manage.py seed_menu
python backend/manage.py createsuperuser
python backend/manage.py runserver 127.0.0.1:8000
```

In another terminal:

```sh
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. Staff sign in at `/kitchen`; the superuser also has access to `/owner/dashboard`. Edit dishes and create staff accounts at `/admin/` through the same frontend origin. Keep the same hostname throughout so session cookies are shared. No default passwords are shipped.

Local mode uses SQLite and in-memory Channels/cache for one ASGI process. It supports UI development but does **not** prove concurrent stock locking. Production explicitly requires PostgreSQL and Redis. `runserver` uses Daphne because it is installed first in Django apps.

## Deploy on Render

### Free prototype on an existing web service

Render's Free web service has no Shell or pre-deploy command. The container's [start-web.sh](backend/start-web.sh) now runs migrations and the one-time bootstrap before starting Daphne. If you already have a Render web service:

1. Set its runtime to Docker, repository root as build context, and the repository [Dockerfile](Dockerfile). Clear any **Docker Command** override so the Dockerfile's startup command runs. Health check path can remain `/healthz`; repeated `200` responses and detection of port `10000` are normal Render probes, not proof that the database or menu works.
2. In the web service's **Environment** page, set `DEBUG=false`, `LOCAL_MODE=false`, `TRUST_PROXY_SSL_HEADER=true`, and a long random `SECRET_KEY`. Set `DATABASE_URL` to the Supabase PostgreSQL **session pooler** URI on port 5432 with `sslmode=require` if the direct URI cannot connect over IPv6. Set `REDIS_URL` to the full **internal connection string** of a Render Key Value instance in the same region; verify the port is complete. Do not enter credentials in Git, Blueprint YAML, commit messages, or build arguments.
3. Temporarily set `BOOTSTRAP_ADMIN_USERNAME` and a unique strong `BOOTSTRAP_ADMIN_PASSWORD` on the web service. On the first restart, the admin is created in Supabase; later restarts do not reset its password. After the logs say `Bootstrap admin created.`, **remove both bootstrap admin variables from Render in the same edit**. The local SQLite superuser is separate and is not transferred to Supabase.
4. The prototype startup adds missing dishes from a 29-item sample catalog across all six categories. Existing prices, stock and availability are never overwritten. Legacy repeated sample images are replaced with distinct photos, while operator-provided custom URLs are preserved. No Shell is needed; remove any existing `BOOTSTRAP_SAMPLE_MENU=false` setting to enable this. Set `BOOTSTRAP_SAMPLE_MENU=false` to manage the menu entirely yourself. If you also set `CLOUDINARY_URL` and `BOOTSTRAP_CLOUDINARY_IMAGES=true`, sample images are copied to Cloudinary. Otherwise they retain their Unsplash URLs. Images and prices are illustrative; verify dishes, prices, tax, fees, descriptions and coverage before accepting public real-money orders.
5. Deploy the latest `main` branch. Check for migration and bootstrap success in the deploy logs. Visit `/api/menu` to verify Supabase connectivity and menu data, then `/kitchen` to sign in. The `/healthz` endpoint only confirms the web process is responding. An empty menu means `BOOTSTRAP_SAMPLE_MENU=false` is set or the bootstrap command did not run; a `500` from `/api/menu` means inspect database connection or migrations.

No paid Celery worker is needed for browsing, checkout, tracking, and kitchen status updates. Network printing needs a separate worker that can reach the kitchen printer and is unavailable in this simple free prototype. Free Render Key Value is memory-only and Free web services can spin down; use paid instances for operational reliability. Never expose the printer's port 9100 publicly.

### Paid Blueprint

The supplied [render.yaml](render.yaml) and [Dockerfile](Dockerfile) deploy the React build and Django/Channels API as **one Render web service** under one hostname. The Blueprint also defines a Redis-compatible Render Key Value instance and a separate Celery worker. The web service has a migration pre-deploy command. The worker and Key Value are paid resources in this Blueprint; review Render's current pricing before creating them. A free web instance is unsuitable for live kitchen operations because it spins down when idle.

1. Push this repository to your Git provider. In Supabase, create a PostgreSQL project. Copy its **direct** connection URL if IPv6 connectivity works, or the **session pooler** URL on port 5432 if you need IPv4. Append `?sslmode=require` (or `&sslmode=require` if the URL already has parameters). Avoid the transaction pooler on port 6543 for this persistent Django server.
2. In Render, choose **New → Blueprint**, select this repository and review the three resources in [render.yaml](render.yaml). Provide `DATABASE_URL` when prompted. The Blueprint generates `SECRET_KEY`, links Redis to the web and worker, enables HTTPS proxy handling, and runs migrations before the web service goes live. Keep the URL and other secrets in Render environment variables, never in the repository.
3. After deploy, visit the Render web URL. Use the **web service Shell** to run `cd backend && python manage.py createsuperuser`. The local `bfc_admin` account lives only in your local SQLite database; it does **not** carry over to Supabase. For a custom domain, add that exact hostname to the web service's `ALLOWED_HOSTS` environment variable, preserving any existing allowed hostnames. The default `onrender.com` hostname is added automatically.
4. Confirm the restaurant's menu prices, tax, fee and delivery zones. Then add dishes through `/admin/`. Alternatively, seed the illustrative catalog once with `cd backend && python manage.py seed_menu`; only do this after verifying and editing the sample data. Set `CLOUDINARY_URL` on the service before `seed_menu --cloudinary` if you want images copied from Unsplash to Cloudinary. Without that, the sample catalog uses direct Unsplash URLs. The images illustrate food, not verified photographs of the restaurant's dishes.
5. Test `/healthz`, `/api/menu`, `/kitchen`, checkout, and a kitchen status update. Confirm that the browser uses `wss://<your-render-host>/ws/...` and reconnects after a service restart. The Docker build includes the frontend and collects its static assets; no second frontend service or reverse-proxy configuration is required.

**Kitchen printer:** The Render worker cannot usually access a thermal printer on the restaurant's private network. Printing remains disabled until `PRINTER_HOST` is configured on both web and worker, and the worker has a secure route to the printer's port 9100. A practical alternative is running the Celery worker on an on-premises kitchen machine with a securely reachable Redis broker and Supabase connection. Never expose the printer's raw port directly to the public internet. Other queue features can run on the Render worker without a printer.

**Vercel alternative:** You can host the Vite output as a Vercel static site and Django as a Render web service. That requires changing the frontend's `/api` and `/ws` same-origin URLs, handling cross-site session cookies/CSRF, and routing WebSockets directly to Render. A Vercel rewrite can proxy HTTP API calls, but Vercel Functions do not serve as a WebSocket server. The single-host Render setup above works with this repository's current session and WebSocket design.

For other hosts, configure [backend/.env.example](backend/.env.example): `DEBUG=false`, `LOCAL_MODE=false`, a random secret, exact hosts and HTTPS origins, Supabase `DATABASE_URL`, and a Redis URL supporting TCP pub/sub (a REST-only Redis endpoint is unsuitable). The Django ORM uses Supabase PostgreSQL directly; it does not use Supabase's public client API. Keep the order tables private from public Supabase API access. Only enable `TRUST_PROXY_SSL_HEADER` behind a trusted HTTPS reverse proxy.

`manage.py check --deploy` may warn about HSTS subdomain inclusion and preloading. Those are intentionally off for the default shared `onrender.com` domain. Enable the corresponding settings only after moving to a domain you control and verifying HTTPS on all its subdomains.

Menu prices, delivery pincodes, 5% tax and ₹40 delivery fee are **sample configuration, not verified restaurant rates or tax advice**. Confirm them with the operator before accepting public orders. Run the seed command only when intentionally resetting sample catalog data. It preserves existing stock and availability. Confirm image suitability and licensing before publication.

## Behavior and security

### Owner dashboard

`/owner/dashboard` requires an active Django superuser. Kitchen staff accounts cannot access owner analytics or controls. The dashboard provides live order counts, completed-order value and trends, preparation/acceptance timing, cancellation reasons, top dishes, staff shifts, emergency ordering pause, store open/close, and per-portion availability. Add existing staff accounts to the shift roster on the dashboard; create their accounts first in Django admin. Both pause and sold-out changes reach storefronts through `/ws/store/`, with periodic HTTP reconciliation. The checkout transaction also checks the locked store setting, so a stale browser cannot place an order while paused. The **Sample data preview** toggle displays labelled, finished example orders seeded on startup; it never adds them to live kitchen operations or real sales. Set `BOOTSTRAP_DEMO_ANALYTICS=false` to disable seeding new examples.

Sales periods use the order's completion time. Existing completed orders are backfilled to their creation time when the new migration runs because historic completion timestamps were not stored. The dashboard reports **completed order value**, not collected revenue: deferred cash payments remain `UNPAID`. Net contribution subtracts recorded delivery subsidies and offer discounts, both zero by default; it does not subtract food, labour, or other costs. Confirm those figures with cash reconciliation before treating them as financial statements.

- All monetary values are integer paise. Server quote and checkout independently calculate totals, tax and delivery fee. Quotes don't reserve stock; checkout totals can change if menu prices change before submission. The final order shows the committed total.
- Checkout locks session and dish rows in a transaction, aggregates duplicate dish quantities, checks stock, and writes immutable item name/portion/price snapshots. A per-checkout UUID provides retry idempotency. Stock is restored once on allowed cancellation.
- `PAID` means **awaiting acceptance** for this deferred-payment workflow. `payment_status=UNPAID` remains explicit; no online payment is collected and no cash collection/reconciliation feature is implemented.
- Customer order HTTP and WebSocket access requires the originating session cookie. Staff endpoints require an authenticated staff account. Session authentication and explicit CSRF protection cover guest checkout and staff login; DRF enforces staff CSRF on mutations. Checkout/login/printing are rate-limited; shared Redis enables cross-process limits. DRF throttles are best-effort, not a strict distributed abuse firewall; add edge limits for public production traffic. There is no OTP endpoint or claim of verified phone ownership.
- Allowed transitions: pending → paid → accepted → preparing → ready → dispatched (delivery) / collected (pickup) → completed. Cancellation is allowed before preparing. Invalid transitions fail. Acceptance timestamps are set by the server.
- WebSockets announce changes without customer data. Clients fetch authorized state on open/reconnect and every 15 seconds. Failed publication does not roll back committed orders.
- Enable the kitchen bell once per browser session (browser autoplay policy). A synthesized Web Audio two-tone bell repeats while new orders remain. Accepting all new orders silences it. Printer tasks intentionally do not retry automatically because network acknowledgements cannot guarantee exactly-once paper printing.
- Delivery coverage is based on configured pincodes; optional coordinates are stored by the API but not geofenced. Customer checkout uses address/pincode entry, not a map picker.
- Persistent cart values are untrusted UI estimates; the backend receives only dish IDs, quantities and customization. Portion variants are separate Dish records sharing a name.

## Verification

```sh
python backend/manage.py test store
python backend/manage.py check
cd frontend
npm run build
```

Tests cover price tampering, immutable snapshots, retry idempotency, stock limits, negative quantities, CSRF, delivery coverage, customer isolation, owner and staff permissions, store pause, sold-out toggles, shift roster, owner analytics, state transitions, cancellation restocking, quote side effects and printer control-byte sanitization. Real PostgreSQL contention, hosted Redis fanout, Cloudinary upload and physical printing require their configured services and should be verified before deployment.

## Source map

- [Models and state engine](backend/store/models.py)
- [Checkout and HTTP endpoints](backend/store/views.py), [server price calculation](backend/store/services.py)
- [WebSocket consumer](backend/store/consumers.py), [routing](backend/store/routing.py)
- [Print task](backend/store/tasks.py), [ESC/POS formatter](backend/store/kitchen_printer.py)
- [Persistent cart](frontend/src/CartContext.tsx), [menu](frontend/src/MenuScreen.tsx), [checkout](frontend/src/CheckoutModal.tsx)
- [Kitchen dashboard](frontend/src/KitchenDashboard.tsx), [tracking](frontend/src/OrderTracking.tsx)
- [Owner models](backend/owner/models.py), [owner API](backend/owner/views.py), [owner dashboard](frontend/src/pages/OwnerDashboard.tsx)
