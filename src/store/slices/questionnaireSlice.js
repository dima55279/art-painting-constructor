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
      state.answers[field] = value
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