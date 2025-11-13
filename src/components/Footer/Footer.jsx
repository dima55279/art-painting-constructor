import React from 'react'
import { useSelector } from 'react-redux'
import styles from './Footer.module.css'

const Footer = () => {
  const { isDark } = useSelector((state) => state.theme)
  const themeClass = isDark ? styles.dark : styles.light

  return (
    <footer className={`${styles.footer} ${themeClass}`}>
      <div className={styles.container}>
        <div className={styles.footerContent}>
          <p className={styles.themeText}>Команда "АЦП-30"</p>
          <p className={styles.themeText}>Проект - Art Painting Constructor</p>
          <p className={styles.themeText}>(С) 2025-2026</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer