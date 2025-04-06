import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

// Common animation variants for page transitions
const pageVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 }
};
const pageTransition = { duration: 0.5, ease: "easeInOut" };
const textVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 }
};

// 1. Login Page
function LoginPage({ onLogin }) {
  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={pageTransition}
    >
      <div className="page-card">
        <motion.h1 className="login-title" variants={textVariants}>
          Welcome Back
        </motion.h1>
        <motion.p className="login-subtitle" variants={textVariants}>
          Please click the button below to login
        </motion.p>
        <motion.button
          className="blue-button"
          onClick={onLogin}
          whileHover="hover"
          whileTap="tap"
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        >
          Login
        </motion.button>
      </div>
    </motion.div>
  );
}

// 2. Main Page
function MainPage({ onLogout, onExplore }) {
  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={pageTransition}
    >
      {/* Logout button at the top-right of the entire page */}
      <motion.button
        className="logout-top-right-page"
        variants={textVariants}
        onClick={onLogout}
        whileHover="hover"
        whileTap="tap"
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      >
        Logout
      </motion.button>

      <motion.h1
        className="main-title"
        variants={textVariants}
        initial="hidden"
        animate="visible"
        transition={{ delay: 0.1, ...pageTransition }}
      >
        My Podcast Recommendations
      </motion.h1>

      <div className="page-card">
        <section>
          <motion.h2
            className="hero-title-bigger"
            variants={textVariants}
            initial="hidden"
            animate="visible"
            transition={{ delay: 0.2, ...pageTransition }}
          >
            Discover Amazing Podcasts
          </motion.h2>
          <motion.p
            className="hero-subtitle-bigger"
            variants={textVariants}
            initial="hidden"
            animate="visible"
            transition={{ delay: 0.3, ...pageTransition }}
          >
            Let's gather some of your interests
          </motion.p>
          <motion.button
            className="blue-button"
            onClick={onExplore}
            whileHover="hover"
            whileTap="tap"
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            style={{ marginTop: '20px' }}
          >
            Get Started
          </motion.button>
        </section>
      </div>

      <footer className="footer">
        <p>&copy; 2025 My Podcast Recommendations</p>
      </footer>
    </motion.div>
  );
}

// 3. First Interests Page
function InterestsPage({ onNext, interests1, setInterests1 }) {
  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={pageTransition}
    >
      <div className="page-card">
        <motion.h1
          className="interests-title"
          variants={textVariants}
          transition={{ delay: 0.1, ...pageTransition }}
        >
          What topics are you interested in?
        </motion.h1>
        <motion.textarea
          className="interests-textarea"
          placeholder="Type your interests here..."
          value={interests1}
          onChange={(e) => setInterests1(e.target.value)}
          variants={textVariants}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.2, ...pageTransition }}
        />
        <motion.button
          className="blue-button"
          onClick={onNext}
          whileHover="hover"
          whileTap="tap"
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          style={{ marginTop: '20px' }}
        >
          Next
        </motion.button>
      </div>
    </motion.div>
  );
}

// 4. Second Interests Page
function InterestsPage2({ onFinish, interests2, setInterests2 }) {
  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={pageTransition}
    >
      <div className="page-card">
        <motion.h1
          className="interests-title"
          variants={textVariants}
          transition={{ delay: 0.1, ...pageTransition }}
        >
          What do you look for in a podcast?
        </motion.h1>
        <motion.textarea
          className="interests-textarea"
          placeholder="Type the aspects here..."
          value={interests2}
          onChange={(e) => setInterests2(e.target.value)}
          variants={textVariants}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.2, ...pageTransition }}
        />
        <motion.button
          className="blue-button"
          onClick={onFinish}
          whileHover="hover"
          whileTap="tap"
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          style={{ marginTop: '20px' }}
        >
          Finish
        </motion.button>
      </div>
    </motion.div>
  );
}

// App
function App() {
  const [page, setPage] = useState('login');
  const [interests1, setInterests1] = useState('');
  const [interests2, setInterests2] = useState('');

  const handleLogin = () => setPage('main');
  const handleLogout = () => setPage('login');
  const handleExplore = () => setPage('interests');
  const handleNext = () => setPage('interests2');
  const handleFinish = () => setPage('main');

  return (
    <div className="App">
      <AnimatePresence mode="wait">
        {page === 'login' && (
          <LoginPage key="login" onLogin={handleLogin} />
        )}
        {page === 'main' && (
          <MainPage
            key="main"
            onLogout={handleLogout}
            onExplore={handleExplore}
          />
        )}
        {page === 'interests' && (
          <InterestsPage
            key="interests"
            interests1={interests1}
            setInterests1={setInterests1}
            onNext={handleNext}
          />
        )}
        {page === 'interests2' && (
          <InterestsPage2
            key="interests2"
            interests2={interests2}
            setInterests2={setInterests2}
            onFinish={handleFinish}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
