import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Room from "./pages/Room";
import Problems from "./pages/Problems";
import ProblemDetail from "./pages/ProblemDetail";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b bg-white">
        <nav className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-4">
          <Link to="/" className="font-semibold tracking-tight">
            leetcode_game
          </Link>
          <Link to="/problems" className="text-sm hover:underline">
            Problems
          </Link>
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/problems" element={<Problems />} />
          <Route path="/problems/:id" element={<ProblemDetail />} />
          <Route path="/room/:roomId" element={<Room />} />
        </Routes>
      </main>
    </div>
  );
}