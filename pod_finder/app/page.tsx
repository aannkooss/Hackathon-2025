'use client'; // Ensure this component is rendered on the client side

import { getServerSession } from "next-auth";
import { signIn } from "next-auth/react"; // Import signIn from NextAuth

const Login = () => {
  // Function to handle the GitHub sign-in button click
  const handleGitHubLogin = () => {
    // Trigger the GitHub OAuth login flow via NextAuth
    signIn("github");
  };


  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500">
      {/* Main container with a background gradient for a visually appealing look */}

      <div className="bg-white p-8 rounded-lg shadow-lg w-96">
        {/* Card containing the login form */}
        
        <h1 className="text-4xl font-extrabold text-center text-gray-800 mb-6">
          Podcast Finder
        </h1>
        {/* Title of the website, larger and bolder to grab attention */}

        {/* "Continue with GitHub" Button */}
        <button
          onClick={handleGitHubLogin}
          className="w-full py-3 px-4 bg-gradient-to-r from-gray-800 to-gray-900 text-white font-semibold rounded-lg hover:bg-gradient-to-l transition duration-300 flex items-center justify-center"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 mr-2"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M12 2C6.48 2 2 6.48 2 12c0 4.41 2.87 8.16 6.85 9.44.5.09.68-.22.68-.47 0-.24-.01-.88-.01-1.73-2.79.6-3.37-1.34-3.37-1.34-.45-1.16-1.1-1.47-1.1-1.47-.91-.62.07-.61.07-.61.99.07 1.51 1.02 1.51 1.02.88 1.5 2.3 1.07 2.87.82.09-.64.34-1.07.62-1.32-2.21-.25-4.54-1.1-4.54-4.9 0-1.08.39-1.96 1.02-2.65-.1-.26-.45-.72-.02-.99 1.16-.1 2.39-.58 2.39-2.62 0-1.09-.43-1.95-1.12-2.63.11-.28.46-.75.17-1.04-.72-.04-1.53-.09-2.26-.26-.14-.28-.27-.56-.38-.86-.08-.08-.08-.16-.09-.24-.01-.08-.01-.17-.01-.26 0-2.49 2.02-4.51 4.51-4.51 2.47 0 4.5 2.02 4.5 4.51 0 .12-.01.24-.02.36-.03.08-.07.15-.09.23-.06.17-.12.33-.19.49.91-.09 1.84-.34 2.74-.85-.34.94-1.04 1.52-1.88 1.97-.85.47-1.86.78-2.93.9 1.05-.91 1.82-2.26 1.82-3.75 0-2.49-2.01-4.5-4.5-4.5z"
              clipRule="evenodd"
            />
          </svg>
          Continue with GitHub
        </button>
        {/* Button styled as GitHub sign-in, with an icon and text */}
      </div>
    </div>
  );
};

export default Login;
