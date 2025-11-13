import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { selectFrame } from '../../store/slices/frameSlice'
import styles from './FrameSelection.module.css'

const FrameSelection = () => {
  const dispatch = useDispatch()
  const { frames, selectedFrame } = useSelector((state) => state.frame)
  const { isDark } = useSelector((state) => state.theme)

  const handleFrameSelect = (frameId) => {
    dispatch(selectFrame(frameId))
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={`${styles.frameSelection} ${themeClass}`}>
      <h3 className={styles.themeText}>Выбор рамки</h3>
      <div className={styles.frames}>
        {frames.map((frame) => (
          <div
            key={frame.id}
            className={`${styles.frame} ${themeClass} ${
              selectedFrame === frame.id ? styles.selected : ''
            }`}
            onClick={() => handleFrameSelect(frame.id)}
          >
            {frame.name}
          </div>
        ))}
      </div>
      
      {selectedFrame && (
        <div className={`${styles.framePreview} ${themeClass}`}>
          <h4 className={styles.themeText}>Выбрана рамка</h4>
          <div className={`${styles.selectedFrameInfo} ${themeClass}`}>
            {frames.find(f => f.id === selectedFrame)?.name}
          </div>
        </div>
      )}
    </div>
  )
}

export default FrameSelection