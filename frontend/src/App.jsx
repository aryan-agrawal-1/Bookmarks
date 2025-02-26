import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'

// queryClient manages caching, invalidation and background updates of our queries
const queryClient = new QueryClient();

function App() {

  return (
    // makes the queryClient available to all components as the client prop is set to queryClient
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path= '/login' element = {<LoginPage />}/>
          <Route path= '/register' element = {<RegisterPage />}/>
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
