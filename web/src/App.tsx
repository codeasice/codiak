import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ToolDirectory from './components/ToolDirectory'
import ToolPage from './components/ToolPage'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<ToolDirectory />} />
        <Route path="/tool/:toolId" element={<ToolPage />} />
      </Routes>
    </Layout>
  )
}
