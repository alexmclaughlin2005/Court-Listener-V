import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import CaseDetailPage from './pages/CaseDetailPage'
import SearchPage from './pages/SearchPage'
import CitationNetworkPage from './pages/CitationNetworkPage'
import CitationAnalyticsPage from './pages/CitationAnalyticsPage'
import TreatmentHistoryPage from './pages/TreatmentHistoryPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/case/:id" element={<CaseDetailPage />} />
        <Route path="/cases/:id/treatment-history" element={<TreatmentHistoryPage />} />
        <Route path="/citations/network/:opinionId" element={<CitationNetworkPage />} />
        <Route path="/citation-network/:opinionId" element={<CitationNetworkPage />} />
        <Route path="/citations/analytics/:opinionId" element={<CitationAnalyticsPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

