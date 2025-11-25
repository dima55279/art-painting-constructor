import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  answers: {
    setting: '',
    clothing: '',
    pose: '',
    additional_notes: '',
    translated_prompt: '', // Добавляем поле для переведенного промпта
    questionnaire_id: null, // Добавляем поле для ID анкеты
  },
}

export const questionnaireSlice = createSlice({
  name: 'questionnaire',
  initialState,
  reducers: {
    setAnswer: (state, action) => {
      const { field, value } = action.payload
      // Разрешаем установку любых полей в answers
      state.answers[field] = value
    },
    clearAnswers: (state) => {
      state.answers = {
        setting: '',
        clothing: '',
        pose: '',
        additional_notes: '',
        translated_prompt: '',
        questionnaire_id: null,
      }
    },
    // Добавляем специальный reducer для установки переведенного промпта
    setTranslatedPrompt: (state, action) => {
      state.answers.translated_prompt = action.payload.prompt
      state.answers.questionnaire_id = action.payload.questionnaire_id
    },
  },
})

export const { setAnswer, clearAnswers, setTranslatedPrompt } = questionnaireSlice.actions
export default questionnaireSlice.reducer