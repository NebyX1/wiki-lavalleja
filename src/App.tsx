import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Articles from "./pages/Articles";
import NotFound from "./pages/NotFound";
import ThemeInitializer from "./components/ThemeInitializer";

export default function App() {
  return (
    <>
      <ThemeInitializer />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="articulos/:slug" element={<Articles />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  );
}
