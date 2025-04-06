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

// Button animation variants
const buttonVariants = {
  hover: { scale: 1.05 },
  tap: { scale: 0.95 }
};

// Reusable BackArrow component (shorter blue button with an arrow)
function BackArrow({ onClick }) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={buttonVariants.hover}
      whileTap={buttonVariants.tap}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      style={{
        position: 'absolute',
        bottom: '10px',
        left: '10px',
        padding: '6px 8px',
        fontSize: '1.2rem',
        background: '#d3d3d3', // lighter gray background
        color: 'black',        // dark text
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      }}
    >
      ←
    </motion.button>
  );
}

// Loading Spinner Component
function LoadingSpinner() {
  return <div className="spinner"></div>;
}

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

// 2. Main Page (back arrow goes to login)
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
      <motion.h1
        className="main-title"
        variants={textVariants}
        initial="hidden"
        animate="visible"
        transition={{ delay: 0.1, ...pageTransition }}
      >
        My Podcast Recommendations
      </motion.h1>

      <div className="page-card" style={{ position: 'relative' }}>
        <section>
          <div className="hero-container">
            <motion.h2
              className="hero-title-bigger"
              variants={textVariants}
              initial="hidden"
              animate="visible"
              transition={{ delay: 0.2, ...pageTransition }}
              style={{ whiteSpace: 'nowrap' }}
            >
              Let's Gather Some Of Your Interests
            </motion.h2>
          </div>
          <div className="button-container">
            <motion.button
              className="blue-button"
              onClick={onExplore}
              whileHover={buttonVariants.hover}
              whileTap={buttonVariants.tap}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              I'm New To Podcasts
            </motion.button>
            <motion.button
              className="blue-button"
              onClick={onKnowWhatILike}
              whileHover={buttonVariants.hover}
              whileTap={buttonVariants.tap}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              I Know What I Like
            </motion.button>
          </div>
        </section>
        {/* Back arrow that returns to the Login page */}
        <BackArrow onClick={onLogout} />
      </div>

      <footer className="footer">
        <p>&copy; 2025 My Podcast Recommendations</p>
      </footer>
    </motion.div>
  );
}

// 3. First Interests Page (back arrow returns to Main)
function InterestsPage({ onNext, interests1, setInterests1, onBack }) {
  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={pageTransition}
    >
      <div className="page-card" style={{ position: 'relative' }}>
        <motion.h1
          className="interests-title"
          variants={textVariants}
          transition={{ delay: 0.1, ...pageTransition }}
        >
          What Topics Are You Interested In?
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
        <BackArrow onClick={onBack} />
      </div>
    </motion.div>
  );
}

// 4. Second Interests Page (back arrow returns to Interests)
function InterestsPage2({ onFinish, interests2, setInterests2, onBack, loading }) {
  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={pageTransition}
    >
      <div className="page-card" style={{ position: 'relative' }}>
        <motion.h1
          className="interests-title"
          variants={textVariants}
          transition={{ delay: 0.1, ...pageTransition }}
        >
          What Do You Look For In A Podcast?
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
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          {loading ? (
            <LoadingSpinner />
          ) : (
            <motion.button
              className="blue-button"
              onClick={onFinish}
              whileHover={buttonVariants.hover}
              whileTap={buttonVariants.tap}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              Finish
            </motion.button>
          )}
        </div>
        <BackArrow onClick={onBack} />
      </div>
    </motion.div>
  );
}

// 5. Podcasts Page (back arrow returns to Main)
function PodcastsPage({ onFinishPodcasts, podcasts, setPodcasts, onBack, loading }) {
  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={pageTransition}
    >
      <div className="page-card" style={{ position: 'relative' }}>
        <motion.h1
          className="interests-title"
          variants={textVariants}
          transition={{ delay: 0.1, ...pageTransition }}
        >
          List Podcasts That You Like
        </motion.h1>
        <motion.p
          variants={textVariants}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.15, ...pageTransition }}
          style={{
            fontSize: '0.8rem',
            color: '#000',  // darker black
            textAlign: 'center',
            marginTop: '-10px',
            marginBottom: '10px'
          }}
        >
          (Separate Answers With Commas)
        </motion.p>
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
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          {loading ? (
            <LoadingSpinner />
          ) : (
            <motion.button
              className="blue-button"
              onClick={onFinishPodcasts}
              whileHover={buttonVariants.hover}
              whileTap={buttonVariants.tap}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              Finish
            </motion.button>
          )}
        </div>
        <BackArrow onClick={onBack} />
      </div>
    </motion.div>
  );
}

// 6. Recommendations Page (back arrow returns to Main)
// 6. Enhanced Recommendations Page
function RecommendationsPage({ recommendations, onReturnMain }) {
  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={pageTransition}
    >
      <div className="page-card" style={{ position: 'relative', padding: '40px' }}>
        <div className="recommendation-header" style={{ marginBottom: '30px' }}>
          <motion.h1 
            className="interests-title"
            variants={textVariants}
            transition={{ delay: 0.1, ...pageTransition }}
            style={{ 
              fontSize: '2.2rem',
              marginBottom: '10px',
              color: '#2c3e50'
            }}
          >
            Your Top Podcast Recommendations
          </motion.h1>
          <motion.p
            variants={textVariants}
            transition={{ delay: 0.15, ...pageTransition }}
            style={{
              fontSize: '1.1rem',
              color: '#7f8c8d',
              textAlign: 'center'
            }}
          >
            Based on your preferences
          </motion.p>
        </div>
        
        <div className="recommendations-list" style={{ width: '100%' }}>
          {recommendations.slice(0, 3).map((rec, index) => (
            <motion.div 
              key={index}
              className="recommendation-item"
              variants={textVariants}
              initial="hidden"
              animate="visible"
              transition={{ delay: 0.2 + (index * 0.1), ...pageTransition }}
              style={{
                backgroundColor: '#f8f9fa',
                borderRadius: '10px',
                padding: '20px',
                marginBottom: '15px',
                boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
              }}
            >
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px'
              }}>
                <h3 style={{ 
                  margin: 0,
                  fontSize: '1.4rem',
                  color: '#2c3e50'
                }}>
                  {rec.podcast_name}
                </h3>
                {rec.similarity_score && (
                  <div style={{
                    backgroundColor: '#e3f2fd',
                    padding: '5px 10px',
                    borderRadius: '20px',
                    fontSize: '0.9rem'
                  }}>
                    <strong>{(rec.similarity_score * 100).toFixed(1)}% match</strong>
                  </div>
                )}
              </div>
              
              <div style={{
                width: '100%',
                height: '8px',
                backgroundColor: '#e0e0e0',
                borderRadius: '4px',
                overflow: 'hidden',
                marginTop: '10px'
              }}>
                <div 
                  style={{
                    width: `${rec.similarity_score * 100}%`,
                    height: '100%',
                    backgroundColor: '#4caf50',
                    borderRadius: '4px'
                  }}
                />
              </div>
            </motion.div>
          ))}
        </div>
        
        <BackArrow onClick={onReturnMain} />
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
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = () => setPage('main');
  const handleLogout = () => setPage('login');
  const handleExplore = () => setPage('interests');
  const handleKnowWhatILike = () => setPage('podcasts');
  const handleNext = () => setPage('interests2');

  // For InterestsPage and PodcastsPage, back arrow returns to Main
  const handleBackToMain = () => setPage('main');
  // For InterestsPage2, back arrow returns to InterestsPage
  const handleBackToInterests = () => setPage('interests');

  // Finish function for interests flow (using API call from second snippet)
  const handleFinish = async () => {
    setIsLoading(true);
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
      
      // Store the recommendations and go to recommendations page
      const recs = data.recommendations;
      setRecommendations(recs && recs.length > 0 ? recs : [{ podcast_name: "No Recommendations Available" }]);
      setPage('recommendations');
      
    } catch (error) {
      console.error('Error sending interests:', error);
      setRecommendations([{ podcast_name: "No Recommendations Available" }]);
      setPage('recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  // Finish function for podcasts page (using API call from second snippet)
  const handleFinishPodcasts = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:2020/api/podcast_input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ podcasts: podcasts })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Successfully sent interests:', data);
      
      // Check if there are recommendations in the response
      const recs = data.recommendations;
      setRecommendations(!recs || recs.length === 0 ? 
        [{ podcast_name: "No Recommendations Available" }] : recs);
      
      setPage('recommendations');
    } catch (error) {
      console.error('Error sending interests:', error);
      setRecommendations([{ podcast_name: "No Recommendations Available" }]);
      setPage('recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <AnimatePresence mode="wait">
        {page === 'login' && <LoginPage key="login" onLogin={handleLogin} />}
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
            onBack={handleBackToMain}
          />
        )}
        {page === 'interests2' && (
          <InterestsPage2
            key="interests2"
            interests2={interests2}
            setInterests2={setInterests2}
            onFinish={handleFinish}
            onBack={handleBackToInterests}
            loading={isLoading}
          />
        )}
        {page === 'podcasts' && (
          <PodcastsPage
            key="podcasts"
            podcasts={podcasts}
            setPodcasts={setPodcasts}
            onFinishPodcasts={handleFinishPodcasts}
            onBack={handleBackToMain}
            loading={isLoading}
          />
        )}
        {page === 'recommendations' && (
          <RecommendationsPage
            key="recommendations"
            recommendations={recommendations}
            onReturnMain={handleBackToMain}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;

