import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { setAnswer } from '../../store/slices/questionnaireSlice'
import styles from './Questionnaire.module.css'

const Questionnaire = () => {
  const dispatch = useDispatch()
  const { answers } = useSelector((state) => state.questionnaire)

  const handleInputChange = (field, value) => {
    dispatch(setAnswer({ field, value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    // Здесь будет логика отправки данных
    console.log('Ответы анкеты:', answers)
  }

  return (
    <div className={styles.questionnaire}>
      <h2 className={styles.sectionTitle}>Анкета</h2>
      <hr className={styles.line} />
      
      <form onSubmit={handleSubmit} className={styles.questionnaireForm}>
        <div className={styles.question}>
          <label>В каком сеттинге будет изображен человек?</label>
          <input
            type="text"
            className={styles.textInput}
            placeholder="Текст"
            value={answers.setting}
            onChange={(e) => handleInputChange('setting', e.target.value)}
          />
        </div>
        
        <div className={styles.question}>
          <label>В какой одежде будет изображен человек?</label>
          <input
            type="text"
            className={styles.textInput}
            placeholder="Текст"
            value={answers.clothing}
            onChange={(e) => handleInputChange('clothing', e.target.value)}
          />
        </div>

        <div className={styles.question}>
          <label>В какой позе будет изображен человек?</label>
          <input
            type="text"
            className={styles.textInput}
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