import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../../store/slices/authSlice'
import Header from '../../components/Header/Header'
import Footer from '../../components/Footer/Footer'
import styles from './Registration.module.css'

const Registration = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { isDark } = useSelector((state) => state.theme)
  const [formData, setFormData] = useState({
    username: '',
    phone: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
    // Очищаем ошибку при изменении поля
    if (errors[e.target.name]) {
      setErrors({
        ...errors,
        [e.target.name]: '',
      })
    }
  }

  const validateForm = () => {
    const newErrors = {}

    if (formData.username.length < 3) {
      newErrors.username = 'Имя пользователя должно содержать минимум 3 символа'
    }

    if (!formData.phone.match(/^\+?[78][-\(]?\d{3}\)?-?\d{3}-?\d{2}-?\d{2}$/)) {
      newErrors.phone = 'Введите корректный номер телефона'
    }

    if (!formData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      newErrors.email = 'Введите корректный email'
    }

    if (formData.password.length < 6) {
      newErrors.password = 'Пароль должен содержать минимум 6 символов'
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Пароли не совпадают'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (validateForm()) {
      const userData = {
        username: formData.username,
        email: formData.email,
        phone: formData.phone,
        id: Date.now()
      }
      dispatch(register(userData))
      navigate('/')
    }
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={`${styles.registrationContainer} ${themeClass}`}>
            <h1 className={styles.registrationHeader}>РЕГИСТРАЦИЯ</h1>
            
            <form onSubmit={handleSubmit} className={styles.form}>
              <div className={styles.formGroup}>
                <input
                  className={`${styles.registerTextInput} ${themeClass} ${
                    errors.username ? styles.error : ''
                  }`}
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="Введите имя пользователя"
                  required
                />
                {errors.username && <span className={styles.errorText}>{errors.username}</span>}
              </div>
              
              <div className={styles.formGroup}>
                <input
                  className={`${styles.registerTextInput} ${themeClass} ${
                    errors.phone ? styles.error : ''
                  }`}
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="Введите номер телефона"
                  required
                />
                {errors.phone && <span className={styles.errorText}>{errors.phone}</span>}
              </div>
              
              <div className={styles.formGroup}>
                <input
                  className={`${styles.registerTextInput} ${themeClass} ${
                    errors.email ? styles.error : ''
                  }`}
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Введите электронную почту"
                  required
                />
                {errors.email && <span className={styles.errorText}>{errors.email}</span>}
              </div>
              
              <div className={styles.formGroup}>
                <input
                  className={`${styles.registerTextInput} ${themeClass} ${
                    errors.password ? styles.error : ''
                  }`}
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Введите пароль"
                  required
                />
                {errors.password && <span className={styles.errorText}>{errors.password}</span>}
              </div>
              
              <div className={styles.formGroup}>
                <input
                  className={`${styles.registerTextInput} ${themeClass} ${
                    errors.confirmPassword ? styles.error : ''
                  }`}
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Повторите пароль"
                  required
                />
                {errors.confirmPassword && (
                  <span className={styles.errorText}>{errors.confirmPassword}</span>
                )}
              </div>
              
              <button type="submit" className={styles.btnRegisterSubmit}>
                ЗАРЕГИСТРИРОВАТЬСЯ
              </button>
              
              <div className={styles.formLoginQuestion}>
                <p className={styles.themeText}>
                  Уже есть аккаунт? <Link to="/login">Войти</Link>
                </p>
              </div>
            </form>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Registration