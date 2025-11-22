import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  answers: {
    setting: '',
    clothing: '',
    pose: '',
  },
}

export const questionnaireSlice = createSlice({
  name: 'questionnaire',
  initialState,
  reducers: {
    setAnswer: (state, action) => {
      const { field, value } = action.payload
      // Убедимся, что поле существует в состоянии
      if (state.answers.hasOwnProperty(field)) {
        state.answers[field] = value
      } else {
        console.warn(`Попытка установить несуществующее поле: ${field}`)
      }
    },
    clearAnswers: (state) => {
      state.answers = {
        setting: '',
        clothing: '',
        pose: '',
      }
    },
  },
})

export const { setAnswer, clearAnswers } = questionnaireSlice.actions
export default questionnaireSlice.reducer