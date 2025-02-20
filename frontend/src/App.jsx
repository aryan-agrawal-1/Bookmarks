import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// queryClient manages caching, invalidation and background updates of our queries
const queryClient = new QueryClient();

function App() {

  return (
    // makes the queryClient available to all components as the client prop is set to queryClient
    <QueryClientProvider client={queryClient}>

    </QueryClientProvider>
  )
}

export default App
