import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { toggleTheme } from '../../store/slices/themeSlice'
import { logout } from '../../store/slices/authSlice'
import { Link, useLocation } from 'react-router-dom'
import styles from './Header.module.css'
import logoDark from '../../images/header/logoDark.png'
import logoLight from '../../images/header/logoLight.png'

const Header = () => {
  const dispatch = useDispatch()
  const location = useLocation()
  const { isAuthenticated } = useSelector((state) => state.auth)
  const { isDark } = useSelector((state) => state.theme)

  const handleThemeToggle = () => {
    dispatch(toggleTheme())
  }

  const handleLogout = () => {
    dispatch(logout())
  }

  const isMainPage = location.pathname === '/'
  const themeClass = isDark ? styles.dark : styles.light

  return (
    <header className={`${styles.headerBlock} ${themeClass}`}>
      <div className={styles.headerContainer}>
        <div className={styles.headerContent}>
          <img 
            src={isDark ? logoDark : logoLight}  
            className={styles.headerLogo} 
            alt="Art Painting Constructor" 
          />
          <div className={styles.headerButtons}>
            <Link 
              to="/" 
              className={`${styles.headerBtn} ${isMainPage ? styles.active : ''}`}
            >
              ГЛАВНАЯ
            </Link>
            {isAuthenticated ? (
              <>
                <Link to="/profile" className={styles.headerBtn}>ПРОФИЛЬ</Link>
                <button onClick={handleLogout} className={styles.headerBtn}>ВЫХОД</button>
              </>
            ) : (
              <>
                <Link to="/login" className={styles.headerBtn}>ВХОД</Link>
                <Link to="/registration" className={styles.headerBtn}>РЕГИСТРАЦИЯ</Link>
              </>
            )}
            <button 
              onClick={handleThemeToggle} 
              className={styles.themeBtn}
              aria-label="Сменить тему"
            >
              {isDark ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header