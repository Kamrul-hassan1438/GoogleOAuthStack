import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import './App.css';

function App() {
  const [userInfo, setUserInfo] = useState(null);
  const [tokens, setTokens] = useState({ access: '', refresh: '' });
  const [error, setError] = useState('');

  const handleSuccess = async (credentialResponse) => {
    console.log('Credential:', credentialResponse.credential);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/google-login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: credentialResponse.credential }),
      });

      const data = await response.json();
      console.log('Backend Response:', data);
      console.log('access:', data.access_token);

      if (data.error) {
        setError(data.error);
      } else {
        setUserInfo(data.user);
        setTokens({
          access: data.access_token,
          refresh: data.refresh_token,
        });
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Error:', err);
    }
  };

  const handleError = () => {
    setError('Google Sign-In failed');
    console.error('Login Failed');
  };

  return (
    <div className="container">
      <h1>Signup with Google</h1>
      
      {!userInfo ? (
        <div className="google-btn">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={handleError}
            useOneTap
          />
        </div>
      ) : null}

      {error && <div className="status-message error">{error}</div>}
      
      {userInfo && (
        <div className="user-info">
          <h2>Welcome!</h2>
          <p>Email: <span>{userInfo.email}</span></p>
          <p>Name: <span>{`${userInfo.first_name} ${userInfo.last_name}`.trim()}</span></p>
          <p>Access Token: <span>{tokens.access.slice(0, 20)}...</span></p>
          <p>Refresh Token: <span>{tokens.refresh.slice(0, 20)}...</span></p>
        </div>
      )}
    </div>
  );
}

export default App;