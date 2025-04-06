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

// New button animation variants to improve responsiveness
const buttonVariants = {
  hover: { scale: 1.05 },
  tap: { scale: 0.95 }
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
          Welcome
        </motion.h1>
        <motion.p className="login-subtitle" variants={textVariants}>
          Let's Find You Some Podcasts...
        </motion.p>
        <motion.button
          className="blue-button"
          onClick={onLogin}
          whileHover={buttonVariants.hover}
          whileTap={buttonVariants.tap}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        >
          Get Started
        </motion.button>
      </div>
    </motion.div>
  );
}

// 2. Main Page
function MainPage({ onLogout, onExplore, onKnowWhatILike }) {
  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={pageTransition}
    >
      {/* Logout button at the top-right */}
      <motion.button
        className="logout-top-right-page"
        variants={textVariants}
        onClick={onLogout}
        whileHover={buttonVariants.hover}
        whileTap={buttonVariants.tap}
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
          {/* Hero container with negative margin-top to shift text upward */}
          <div className="hero-container">
            <motion.h2
              className="hero-title-bigger"
              variants={textVariants}
              initial="hidden"
              animate="visible"
              transition={{ delay: 0.2, ...pageTransition }}
              style={{ whiteSpace: 'nowrap' }}
            >
              Let's gather some of your interests
            </motion.h2>
          </div>
          {/* Vertical button container with equal-width buttons */}
          <div className="button-container">
            <motion.button
              className="blue-button"
              onClick={onExplore}
              whileHover={buttonVariants.hover}
              whileTap={buttonVariants.tap}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              I'm new to podcasts
            </motion.button>
            <motion.button
              className="blue-button"
              onClick={onKnowWhatILike}
              whileHover={buttonVariants.hover}
              whileTap={buttonVariants.tap}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              I know what I like
            </motion.button>
          </div>
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
          whileHover={buttonVariants.hover}
          whileTap={buttonVariants.tap}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          style={{ marginTop: '20px' }}
        >
          Next
        </motion.button>
      </div>
    </motion.div>
  );
}

// 4. Second Interests Page with Back Button
function InterestsPage2({ onFinish, interests2, setInterests2, onBack }) {
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
          whileHover={buttonVariants.hover}
          whileTap={buttonVariants.tap}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          style={{ marginTop: '20px' }}
        >
          Finish
        </motion.button>
      </div>
      {/* Back button at bottom left with fade in/out animations */}
      <motion.button
        className="back-button"
        onClick={onBack}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        whileHover={buttonVariants.hover}
        whileTap={buttonVariants.tap}
        transition={{
          opacity: { duration: 0.5 },
          default: { type: 'spring', stiffness: 300, damping: 20 }
        }}
      >
        Back
      </motion.button>
    </motion.div>
  );
}

// 5. Podcasts Page (for users who know what they like)
function PodcastsPage({ onFinishPodcasts, podcasts, setPodcasts }) {
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
          List podcasts that you like
        </motion.h1>
        <motion.textarea
          className="interests-textarea"
          placeholder="Type the podcasts here..."
          value={podcasts}
          onChange={(e) => setPodcasts(e.target.value)}
          variants={textVariants}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.2, ...pageTransition }}
        />
        <motion.button
          className="blue-button"
          onClick={onFinishPodcasts}
          whileHover={buttonVariants.hover}
          whileTap={buttonVariants.tap}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          style={{ marginTop: '20px' }}
        >
          Finish
        </motion.button>
      </div>
    </motion.div>
  );
}

// App Component
function App() {
  const [page, setPage] = useState('login');
  const [interests1, setInterests1] = useState('');
  const [interests2, setInterests2] = useState('');
  const [podcasts, setPodcasts] = useState('');

  const handleLogin = () => setPage('main');
  const handleLogout = () => setPage('login');

  // Navigate to interests flow (for new users)
  const handleExplore = () => setPage('interests');

  // Navigate directly to podcasts page (for users who know what they like)
  const handleKnowWhatILike = () => setPage('podcasts');

  const handleNext = () => setPage('interests2');
  const handleBack = () => setPage('interests');

  // Finish functions that send input to an API endpoint
  const handleFinish = async () => {
    try {
      const response = await fetch('http://localhost:2020/api/interests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interests1, interests2 })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Successfully sent interests:', data);
    } catch (error) {
      console.error('Error sending interests:', error);
    }
    setPage('main');
  };

  const handleFinishPodcasts = async () => {
    try {
      const response = await fetch('http://localhost:2020/api/interests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([interests1])
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Successfully sent interests:', data);
    } catch (error) {
      console.error('Error sending interests:', error);
    }
    setPage('main');
  };

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
            onKnowWhatILike={handleKnowWhatILike}
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
            onBack={handleBack}
          />
        )}
        {page === 'podcasts' && (
          <PodcastsPage
            key="podcasts"
            podcasts={podcasts}
            setPodcasts={setPodcasts}
            onFinishPodcasts={handleFinishPodcasts}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
