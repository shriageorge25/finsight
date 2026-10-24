import { Routes, Route } from "react-router-dom";
import BusinessProvider from "./context/BusinessProvider";
import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import StateBox from "./components/StateBox";
import Inconsistencies from "./components/Inconsistencies";
import Overdue from "./components/Overdue";
import LoanSimulator from "./components/LoanSimulator";
import LatePayers from "./components/LatePayers";

export default function App() {
  return (
    <BusinessProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/loan" element={<LoanSimulator />} />
          <Route path="*" element={<StateBox kind="empty" message="Page not found." />} />
          <Route path="/inconsistencies" element={<Inconsistencies />} />
          <Route path="/overdue" element={<Overdue />} />
          <Route path="/late-payers" element={<LatePayers />} />
        </Route>
      </Routes>
    </BusinessProvider>
  );
}