import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import CaseDetailPage from './pages/CaseDetailPage'
import SearchPage from './pages/SearchPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/case/:caseId" element={<CaseDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

