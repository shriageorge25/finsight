import { createContext, useContext } from "react";

export const BusinessContext = createContext(null);
export const useBusiness = () => useContext(BusinessContext);