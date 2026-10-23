import { Routes, Route } from "react-router-dom";
import BusinessProvider from "./context/BusinessProvider";
import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import StateBox from "./components/StateBox";

export default function App() {
  return (
    <BusinessProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/loan" element={<StateBox kind="empty" message="Loan simulator comes next." />} />
          <Route path="*" element={<StateBox kind="empty" message="Page not found." />} />
        </Route>
      </Routes>
    </BusinessProvider>
  );
}