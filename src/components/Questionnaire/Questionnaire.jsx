import React, { useEffect } from 'react' // Добавляем useEffect
import { useSelector, useDispatch } from 'react-redux'
import { setAnswer, setTranslatedPrompt } from '../../store/slices/questionnaireSlice'
import { useSubmitQuestionnaireMutation } from '../../services/api'
import styles from './Questionnaire.module.css'

const Questionnaire = () => {
  const dispatch = useDispatch()
  const { answers } = useSelector((state) => state.questionnaire)
  const { isDark } = useSelector((state) => state.theme)

  const [submitQuestionnaire, { isLoading }] = useSubmitQuestionnaireMutation()

  // Добавляем useEffect для отслеживания изменений answers
  useEffect(() => {
    console.log('🔄 Answers обновились:', answers)
  }, [answers])

  const handleInputChange = (field, value) => {
    dispatch(setAnswer({ field, value }))
  }

  const validateForm = () => {
    const errors = []
    
    if (!answers.setting || answers.setting.trim() === '') {
      errors.push('Сеттинг не может быть пустым')
    }
    
    if (!answers.clothing || answers.clothing.trim() === '') {
      errors.push('Одежда не может быть пустой')
    }
    
    if (!answers.pose || answers.pose.trim() === '') {
      errors.push('Поза не может быть пустой')
    }
    
    return errors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    console.log('Отправка анкеты:', answers)
    
    const errors = validateForm()
    if (errors.length > 0) {
      alert(`Пожалуйста, заполните все поля:\n${errors.join('\n')}`)
      return
    }
    
    try {
      const result = await submitQuestionnaire({
        setting: answers.setting,
        clothing: answers.clothing,
        pose: answers.pose,
        additional_notes: answers.additional_notes || ''
      }).unwrap()
      
      console.log('Полный ответ от сервера:', JSON.stringify(result, null, 2))
      console.log('Есть ли translated_prompt в ответе?', 'translated_prompt' in result)
      console.log('Значение translated_prompt:', result.translated_prompt)
      
      // Сохраняем переведенный промпт и ID анкеты в Redux
      if (result.translated_prompt) {
        dispatch(setTranslatedPrompt({
          prompt: result.translated_prompt,
          questionnaire_id: result.questionnaire_id
        }))
        console.log('✅ Переведенный промпт сохранен в Redux')
      } else {
        console.log('❌ В ответе нет translated_prompt')
      }
      
      alert(`Анкета отправлена! ID: ${result.questionnaire_id}`)
    } catch (error) {
      console.error('Ошибка отправки анкеты:', error)
      
      let errorMessage = 'Неизвестная ошибка'
      
      if (error.data && error.data.detail) {
        if (typeof error.data.detail === 'string') {
          errorMessage = error.data.detail
        } else if (Array.isArray(error.data.detail)) {
          errorMessage = error.data.detail.map(err => {
            if (err.loc && err.msg) {
              return `${err.loc[1]}: ${err.msg}`
            }
            return err.msg || err.message
          }).join(', ')
        }
      } else if (error.error) {
        errorMessage = error.error
      } else if (error.message) {
        errorMessage = error.message
      }
      
      alert(`Ошибка при отправке анкеты: ${errorMessage}`)
    }
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
            placeholder="Например: фэнтезийный лес, космическая станция"
            value={answers.setting}
            onChange={(e) => handleInputChange('setting', e.target.value)}
            disabled={isLoading}
            required
          />
        </div>
        
        <div className={`${styles.question} ${themeClass}`}>
          <label className={styles.themeText}>В какой одежде будет изображен человек?</label>
          <input
            type="text"
            className={`${styles.textInput} ${themeClass}`}
            placeholder="Например: рыцарские доспехи, космический скафандр"
            value={answers.clothing}
            onChange={(e) => handleInputChange('clothing', e.target.value)}
            disabled={isLoading}
            required
          />
        </div>

        <div className={`${styles.question} ${themeClass}`}>
          <label className={styles.themeText}>В какой позе будет изображен человек?</label>
          <input
            type="text"
            className={`${styles.textInput} ${themeClass}`}
            placeholder="Например: сидит на троне, летит в воздухе"
            value={answers.pose}
            onChange={(e) => handleInputChange('pose', e.target.value)}
            disabled={isLoading}
            required
          />
        </div>
        
        <div className={`${styles.question} ${themeClass}`}>
          <label className={styles.themeText}>Дополнительные заметки (необязательно)</label>
          <input
            type="text"
            className={`${styles.textInput} ${themeClass}`}
            placeholder="Любые дополнительные пожелания..."
            value={answers.additional_notes || ''}
            onChange={(e) => handleInputChange('additional_notes', e.target.value)}
            disabled={isLoading}
          />
        </div>
        
        <button 
          type="submit" 
          className={styles.submitBtn}
          disabled={isLoading || !answers.setting?.trim() || !answers.clothing?.trim() || !answers.pose?.trim()}
        >
          {isLoading ? 'Отправка...' : 'Отправить анкету'}
        </button>
      </form>

    </div>
  )
}

export default Questionnaire