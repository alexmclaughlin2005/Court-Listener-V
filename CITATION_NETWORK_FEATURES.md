# Citation Network Features Documentation

## Overview

The citation network visualization provides an interactive way to explore how legal cases cite each other. Users can click on any node to view detailed case information including opinion text, treatment analysis, and citation relationships.

## Features Implemented

### 1. Interactive Citation Network Visualization

**Location**: [frontend/src/pages/CitationNetworkPage.tsx](frontend/src/pages/CitationNetworkPage.tsx)

**What it does**:
- Displays cases as nodes in a circular graph layout
- Shows citation relationships as directed edges
- Color-codes nodes based on relationship type and treatment
- Supports depth control (1-2 levels) and node limits (25-200 nodes)
- Animated edges for visual clarity

**Node Colors**:
- **Blue** (#3b82f6): Center case (the one you're viewing)
- **Green** (#10b981): Cases that cite this case (inbound)
- **Orange** (#f59e0b): Cases cited by this case (outbound)
- **Red** (#ef4444): Negative treatment (overruled, reversed, etc.)
- **Gray** (#6b7280): Neutral treatment

**Edge Colors**:
- **Green**: Inbound citations (cases citing this one)
- **Orange**: Outbound citations (cases this one cites)

### 2. Treatment Badges

**Component**: [frontend/src/components/TreatmentBadge.tsx](frontend/src/components/TreatmentBadge.tsx)

**Treatment Types with Icons**:
- ⛔ **OVERRULED**: Case law has been explicitly overruled
- 🔴 **REVERSED**: Decision was reversed on appeal
- ⭕ **VACATED**: Decision was vacated
- 🟠 **CRITICIZED**: Case has been criticized by later courts
- 🟡 **QUESTIONED**: Validity has been questioned
- ✅ **AFFIRMED**: Decision was affirmed on appeal
- 🟢 **FOLLOWED**: Case precedent has been followed
- 🔵 **DISTINGUISHED**: Case has been distinguished from others
- 📄 **CITED**: Case was cited (neutral treatment)
- ❓ **UNKNOWN**: Treatment type unknown

**Severity Levels**:
- **NEGATIVE**: Red badge (overruled, reversed, vacated, criticized)
- **POSITIVE**: Green badge (affirmed, followed)
- **NEUTRAL**: Gray badge (distinguished, cited, questioned)

### 3. Case Detail Flyout

**Component**: [frontend/src/components/CaseDetailFlyout.tsx](frontend/src/components/CaseDetailFlyout.tsx)

**What it shows**:
A sliding panel from the right side with three tabs:

#### Tab 1: Opinion
- Full opinion text (HTML or plain text)
- Automatically fetches missing opinion text from CourtListener API
- Formatted with legal document styling
- Shows "Fetching opinion text..." status during API calls
- Gracefully handles cases with no opinion text

#### Tab 2: Treatment
- Shows how this case has been treated by later courts
- Displays treatment type, severity, and confidence score
- Shows depth (how many citation hops away)
- Visual treatment badge with icon

#### Tab 3: Citations
- **Inbound citations**: Cases that cite this one
- **Outbound citations**: Cases that this one cites
- Shows case names, courts, dates, and citation counts
- Includes links to view each case's network

### 4. Automatic Data Fetching

**Backend API**: [backend/app/api/v1/citation_sync.py](backend/app/api/v1/citation_sync.py)

#### Citation Syncing
When opening a case that lacks citation data:
1. Checks if citations exist in database
2. If missing, automatically fetches from CourtListener API v3
3. Imports citations into database
4. Returns updated citation data

**Endpoint**: `POST /api/v1/citation-sync/sync/{opinion_id}`

#### Opinion Text Fetching
When opening a case that lacks opinion text:
1. Detects missing text (no plain_text and no html)
2. Fetches from CourtListener API v4
3. Updates database with retrieved text
4. Returns formatted text for display

**Endpoint**: `POST /api/v1/citations/fetch-opinion-text/{opinion_id}`

### 5. Opinion HTML Formatting

**Styles**: [frontend/src/index.css](frontend/src/index.css) (lines 19-100)

Custom CSS for CourtListener's HTML structure:
- `.opinion-text`: Base container with proper spacing
- `.case_cite`: Case citations in bold
- `.parties`: Party names styled
- `.docket`: Docket number formatting
- `.court`: Court name in italics
- `.date`: Date formatting
- `.prelims`: Preliminary matter styling with border
- `.indent`: Indented paragraphs
- `.num`: Section numbers in bold
- `.footnote`: Superscript footnotes

## URL Routing

**Supported URLs**:
- `/citations/network/:opinionId` - Original route
- `/citation-network/:opinionId` - Alias for compatibility

Both routes render the same CitationNetworkPage component.

## API Endpoints Used

### Citation Network
- `GET /api/v1/citations/network/{opinion_id}?depth=1&max_nodes=50`
  - Returns graph data with nodes and edges
  - Supports depth: 1-2 levels
  - Supports max_nodes: 25-200 nodes

### Case Details
- `GET /api/v1/search/cases/{cluster_id}`
  - Returns full case information
  - Includes opinions, docket, court details

### Treatment Data
- `GET /api/v1/treatment/{opinion_id}`
  - Returns how case has been treated by later courts
  - Includes treatment type, severity, confidence

### Citations
- `GET /api/v1/citations/inbound/{opinion_id}?depth=1&limit=20`
  - Returns cases that cite this opinion

- `GET /api/v1/citations/outbound/{opinion_id}?depth=1&limit=20`
  - Returns cases cited by this opinion

### Automatic Syncing
- `GET /api/v1/citation-sync/check/{opinion_id}`
  - Checks if citations exist for an opinion

- `POST /api/v1/citation-sync/sync/{opinion_id}`
  - Fetches and imports citations from CourtListener API

- `POST /api/v1/citations/fetch-opinion-text/{opinion_id}`
  - Fetches opinion text from CourtListener API

## User Workflow

1. **Search for a case** on the search page
2. **Click "View Network"** on a search result
3. **Interactive graph loads** showing citation relationships
4. **Click any node or card** to open the flyout
5. **Flyout opens** with three tabs (Opinion, Treatment, Citations)
6. **Missing data auto-fetches** from CourtListener API
7. **View formatted opinion text** with legal styling
8. **Explore treatment** to see how case has been treated
9. **Browse citations** to find related cases
10. **Click any citation** to view that case's network

## Technical Architecture

### Frontend Stack
- **React 18** with TypeScript
- **React Flow** for graph visualization
- **React Router** for routing
- **Tailwind CSS** for styling
- **Axios** for API calls

### Backend Stack
- **FastAPI** for API endpoints
- **SQLAlchemy** for database ORM
- **httpx** for async HTTP requests to CourtListener API
- **PostgreSQL** for data storage

### Data Flow
1. User clicks network node
2. Frontend calls multiple APIs in parallel:
   - Case details
   - Treatment data
   - Inbound citations
   - Outbound citations
   - Citation status check
3. If data missing, triggers auto-sync:
   - Fetches from CourtListener API
   - Stores in database
   - Returns to frontend
4. Frontend displays in flyout
5. User interacts with tabs

## Recent Fixes

### Fix 1: httpx Migration
**Issue**: Backend crashed with `ModuleNotFoundError: No module named 'requests'`

**Solution**: Replaced `requests` library with `httpx` (already in requirements.txt)
- Changed to async/await pattern
- Updated exception handling from `requests.RequestException` to `httpx.HTTPError`

### Fix 2: React Flow Rendering
**Issue**: Blank page due to undefined data structures

**Solution**: Added null checks before processing data
```typescript
if (!data.nodes || data.nodes.length === 0) {
  setError('No citation network data available for this opinion')
  setLoading(false)
  return
}
```

### Fix 3: React Hooks Dependencies
**Issue**: Flyout not working when clicking nodes

**Solution**: Wrapped `fetchCaseData` in `useCallback` with proper dependencies
```typescript
const fetchCaseData = React.useCallback(async () => {
  // ... function body
}, [clusterId, opinionId]);
```

### Fix 4: URL Routing
**Issue**: Blank page at `/citation-network/:opinionId`

**Root Cause**: Route defined as `/citations/network/:opinionId` (plural) but URL used `/citation-network/:opinionId` (singular with dash)

**Solution**: Added route alias in App.tsx
```typescript
<Route path="/citation-network/:opinionId" element={<CitationNetworkPage />} />
```

## Environment Variables

### Frontend (Vercel)
- `VITE_API_URL`: Backend API URL
  - Value: `https://court-listener-v-production.up.railway.app`
  - Must be set for all environments (Production, Preview, Development)

### Backend (Railway)
- `COURTLISTENER_API_TOKEN`: API token for CourtListener
- `DATABASE_URL`: PostgreSQL connection string
- `CORS_ORIGINS`: Allowed frontend origins
  - Example: `https://court-listener-v.vercel.app,http://localhost:5173`

## Testing the Features

### Test Citation Network
1. Visit: https://court-listener-v.vercel.app/citation-network/346946
2. Should see interactive graph with 5 nodes
3. Click any node to open flyout

### Test Auto-Fetch
1. Find a case with no opinion text
2. Click "View Network"
3. Click the node to open flyout
4. Click "Opinion" tab
5. Should see "Fetching opinion text from CourtListener..."
6. Text should load and display

### Test Citations
1. Open any case flyout
2. Click "Citations" tab
3. Should see inbound and outbound citations
4. Click "View Network" on any citation
5. Should navigate to that case's network

## Future Enhancements

### Potential Improvements
1. **Force-directed graph layout** - More organic positioning
2. **Zoom and pan controls** - Better navigation for large graphs
3. **Filter by treatment type** - Show only overruled cases
4. **Export graph** - Save as PNG or SVG
5. **Case comparison** - Compare two cases side-by-side
6. **Citation timeline** - Show citations over time
7. **Search within network** - Find specific cases in graph
8. **Keyboard shortcuts** - Navigate with keyboard
9. **Mobile optimization** - Touch-friendly controls
10. **Share links** - Deep links to specific nodes

### Performance Optimizations
1. **Lazy loading** - Load nodes as needed
2. **Virtual scrolling** - For citation lists
3. **Caching** - Cache fetched opinions locally
4. **WebSocket updates** - Real-time data sync
5. **Progressive enhancement** - Load basic view first

---

**Last Updated**: November 17, 2025
**Status**: ✅ All features working and deployed to production
