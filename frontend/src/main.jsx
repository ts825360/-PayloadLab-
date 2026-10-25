import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./workspace.css";
import "./workbench.css";
import "./learning-guide.css";
import "./theme-tokens.css";
import "./unified-workspace.css";
import "./web-workspace.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
