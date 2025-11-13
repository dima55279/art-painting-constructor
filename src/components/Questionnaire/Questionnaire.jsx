import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { setAnswer } from '../../store/slices/questionnaireSlice'
import styles from './Questionnaire.module.css'

const Questionnaire = () => {
  const dispatch = useDispatch()
  const { answers } = useSelector((state) => state.questionnaire)
  const { isDark } = useSelector((state) => state.theme)

  const handleInputChange = (field, value) => {
    dispatch(setAnswer({ field, value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('Ответы анкеты:', answers)
    alert('Анкета отправлена!')
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={`${styles.questionnaire} ${themeClass}`}>
      <h2 className={`${styles.sectionTitle} ${styles.themeText}`}>Анкета</h2>
      <hr className={styles.line} />
      
      <form onSubmit={handleSubmit} className={styles.questionnaireForm}>
        <div className={`${styles.question} ${themeClass}`}>
          <label className={styles.themeText}>В каком сеттинге будет изображен человек?</label>
          <input
            type="text"
            className={`${styles.textInput} ${themeClass}`}
            placeholder="Текст"
            value={answers.setting}
            onChange={(e) => handleInputChange('setting', e.target.value)}
          />
        </div>
        
        <div className={`${styles.question} ${themeClass}`}>
          <label className={styles.themeText}>В какой одежде будет изображен человек?</label>
          <input
            type="text"
            className={`${styles.textInput} ${themeClass}`}
            placeholder="Текст"
            value={answers.clothing}
            onChange={(e) => handleInputChange('clothing', e.target.value)}
          />
        </div>

        <div className={`${styles.question} ${themeClass}`}>
          <label className={styles.themeText}>В какой позе будет изображен человек?</label>
          <input
            type="text"
            className={`${styles.textInput} ${themeClass}`}
            placeholder="Текст"
            value={answers.pose}
            onChange={(e) => handleInputChange('pose', e.target.value)}
          />
        </div>
        
        <button type="submit" className={styles.submitBtn}>
          Отправить запрос
        </button>
      </form>
    </div>
  )
}

export default Questionnaire