# Next Steps Roadmap

## ✅ Completed

- ✅ Backend deployed to Railway
- ✅ Backend is working (health check passes)
- ✅ CORS_ORIGINS configured
- ✅ Frontend configured for port 5173
- ✅ Database initialized with tables
- ✅ Sample data imported (5 courts, 20 cases, 25 opinions, 28 citations)
- ✅ Search API endpoints implemented
- ✅ Citation network API endpoints implemented
- ✅ Frontend deployed to Vercel
- ✅ Frontend connected to backend API
- ✅ Search functionality working
- ✅ TypeScript types configured

## 🎯 Current Status

**Live URLs**:
- Frontend: https://court-listener-v.vercel.app/
- Backend API: https://court-listener-v-production.up.railway.app
- API Docs: https://court-listener-v-production.up.railway.app/docs

**Working Features**:
- ✅ Search cases by name
- ✅ View search results with case details
- ✅ Sort by relevance, date, or citations
- ✅ Backend citation network APIs (ready for frontend)

## 🚀 Next Steps (Priority Order)

### Step 1: Implement Case Detail Page 📄

**Why**: Users can click on search results but there's no detail view yet.

**Tasks**:
1. Create `frontend/src/pages/CaseDetailPage.tsx`
2. Display:
   - Full case information (name, court, date, judges)
   - Opinion text (plain_text or html)
   - Citation count and precedential status
   - Link to citation network visualization
3. Add route in `frontend/src/App.tsx`
4. Style with Tailwind CSS

**API Endpoint**: Already implemented at `/api/v1/search/cases/{case_id}`

### Step 2: Add Citation Network Visualization 🕸️

**Why**: Core feature - visualize how cases cite each other.

**Tasks**:
1. Install D3.js or React Flow: `npm install react-flow-renderer`
2. Create `frontend/src/pages/CitationNetworkPage.tsx`
3. Fetch data from `/api/v1/citations/network/{opinion_id}`
4. Display interactive graph:
   - Center node = current case
   - Outbound edges = cases this one cites
   - Inbound edges = cases that cite this one
5. Add controls for depth and max nodes

**API Endpoints**: Already implemented:
- `/api/v1/citations/network/{opinion_id}` - Graph data
- `/api/v1/citations/inbound/{opinion_id}` - Cases citing this
- `/api/v1/citations/outbound/{opinion_id}` - Cases cited by this

### Step 3: Add Citation Analytics Dashboard 📊

**Why**: Show citation patterns and related cases.

**Tasks**:
1. Create `frontend/src/pages/AnalyticsPage.tsx`
2. Display:
   - Citation timeline (citations over time)
   - Top citing courts
   - Related cases (co-cited cases)
   - Most cited cases overall
3. Add charts using Recharts or Chart.js

**API Endpoints**: Already implemented:
- `/api/v1/citations/analytics/{opinion_id}` - Analytics data
- `/api/v1/citations/most-cited` - Most cited cases

### Step 4: Add Advanced Search Filters 🔍

**Why**: Allow filtering by court, date range, citation count.

**Tasks**:
1. Update `SearchPage.tsx` with filter UI
2. Add date pickers (start/end date)
3. Add court dropdown
4. Add citation count range slider
5. Update API calls with filter parameters

**API Support**: Already implemented in `/api/v1/search/cases`

### Step 5: Import Full CourtListener Dataset 📦

**Why**: Replace sample data with real case law.

**Tasks**:
1. Download CourtListener bulk data
2. Run import scripts:
   ```bash
   railway run python -m app.services.import_csv --file courts.csv
   railway run python -m app.services.import_csv --file opinions.csv
   ```
3. Monitor import progress
4. Verify data integrity

**Current Data**: 5 courts, 20 cases, 25 opinions (sample data)

## 📋 Updated Checklist

### Completed ✅
- [x] Initialize database
- [x] Verify API docs are accessible
- [x] Deploy frontend to Vercel
- [x] Set `VITE_API_URL` in Vercel
- [x] Update backend CORS with Vercel URL
- [x] Test local frontend
- [x] Test Vercel frontend
- [x] Import sample data
- [x] Implement search API
- [x] Implement citation network API
- [x] Build search page UI
- [x] Connect frontend to backend

### In Progress 🚧
- [ ] Implement case detail page
- [ ] Add citation network visualization
- [ ] Add citation analytics dashboard
- [ ] Add advanced search filters
- [ ] Import full dataset

## 🎯 Recommended Next Step

**Build the Case Detail Page** - This is the natural next step since:
1. Search results link to `/case/{id}` but the page doesn't exist yet
2. It's needed before citation network visualization
3. The backend API is already ready
4. It's a straightforward UI task

Would you like me to implement the Case Detail Page now?

