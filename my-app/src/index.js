import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { Auth0Provider } from '@auth0/auth0-react';

const domain = "dev-lc0sijwlre1nfnub.us.auth0.com";
const clientId = "10LWxcUo3FtvbtIxlOOnsCCeq07YupOE";

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Auth0Provider 
      domain = {domain}
      clientId = {clientId}
      authorizationParameters = {{redirect_uri: "http://localhost:3002/auth/github/callback" }}
      >
    <App />
    </Auth0Provider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
