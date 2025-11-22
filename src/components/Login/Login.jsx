import React, { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate, Link } from 'react-router-dom'
import { useLoginMutation } from '../../services/api'
import { setCredentials } from '../../store/slices/authSlice' // Изменено с loginSuccess на setCredentials
import Header from '../Header/Header'
import Footer from '../Footer/Footer'
import styles from './Login.module.css'

const Login = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { isDark } = useSelector((state) => state.theme)
  const [login, { isLoading, error }] = useLoginMutation()

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  })

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.username || !formData.password) {
      return
    }

    try {
      const result = await login(formData).unwrap()
      
      // Изменено с loginSuccess на setCredentials
      dispatch(setCredentials({
        access_token: result.access_token,
        user: result.user
      }))
      
      navigate('/')
    } catch (err) {
      console.error('Login error:', err)
    }
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={`${styles.loginContainer} ${themeClass}`}>
            <h1 className={styles.registrationHeader}>ВХОД</h1>
            
            <form onSubmit={handleSubmit} className={styles.form}>
              {error && (
                <div className={styles.errorMessage}>
                  {error.data?.message || 'Ошибка авторизации'}
                </div>
              )}
              
              <div className={styles.formGroup}>
                <input
                  className={`${styles.loginTextInput} ${themeClass}`}
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="Введите имя пользователя"
                  required
                  disabled={isLoading}
                />
              </div>
              
              <div className={styles.formGroup}>
                <input
                  className={`${styles.loginTextInput} ${themeClass}`}
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Введите пароль"
                  required
                  disabled={isLoading}
                />
              </div>
              
              <button 
                type="submit" 
                className={styles.btnLoginSubmit}
                disabled={isLoading}
              >
                {isLoading ? 'ВХОД...' : 'ВОЙТИ'}
              </button>
              
            </form>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Login