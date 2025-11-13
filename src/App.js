import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Provider } from 'react-redux'
import { store } from './store'
import MainPage from './components/MainPage/MainPage.jsx'
import Login from './components/Login/Login.jsx'
import Registration from './components/Registration/Registration.jsx'
import Profile from './components/Profile/Profile.jsx'
import './index.css'

function App() {
  return (
    <Provider store={store}>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<MainPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/registration" element={<Registration />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </div>
      </Router>
    </Provider>
  )
}

export default App