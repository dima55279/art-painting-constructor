import React from 'react'
import { useSelector } from 'react-redux'
import styles from './Footer.module.css'

const Footer = () => {
  const { isDark } = useSelector((state) => state.theme)

  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.footerContent}>
          <p>Команда "АЦП-30"</p>
          <p>Проект - Art Painting Constructor</p>
          <p>(С) 2025-2026</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer