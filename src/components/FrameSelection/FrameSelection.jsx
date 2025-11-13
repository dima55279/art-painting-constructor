import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { selectFrame } from '../../store/slices/frameSlice'
import styles from './FrameSelection.module.css'

const FrameSelection = () => {
  const dispatch = useDispatch()
  const { frames, selectedFrame } = useSelector((state) => state.frame)

  const handleFrameSelect = (frameId) => {
    dispatch(selectFrame(frameId))
  }

  return (
    <div className={styles.frameSelection}>
      <h3>Выбор рамки</h3>
      <div className={styles.frames}>
        {frames.map((frame) => (
          <div
            key={frame.id}
            className={`${styles.frame} ${selectedFrame === frame.id ? styles.selected : ''}`}
            onClick={() => handleFrameSelect(frame.id)}
          >
            {frame.name}
          </div>
        ))}
      </div>
    </div>
  )
}

export default FrameSelection