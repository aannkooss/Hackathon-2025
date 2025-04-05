import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';  // Import the hook

function App() {
  const { loginWithRedirect, logout, user, isAuthenticated, isLoading } = useAuth0();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="App" style={{ maxWidth: '400px', margin: '50px auto', padding: '20px' }}>
      <h2>Login with GitHub</h2>

      {isAuthenticated ? (
        <div>
          <p>Welcome, {user.name}</p>
          <img src={user.picture} alt="profile" width={60} style={{ borderRadius: '50%' }} />
          <br />
          <button onClick={() => logout({ returnTo: window.location.origin })}>Log out</button>
        </div>
      ) : (
        <button
          onClick={() => loginWithRedirect({ connection: 'github' })} // Trigger GitHub login
          style={{ width: '100%', padding: '10px', backgroundColor: '#333', color: 'white', border: 'none' }}
        >
          Login with GitHub
        </button>
      )}
    </div>
  );
}

export default App;
