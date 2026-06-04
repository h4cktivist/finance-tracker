import { useEffect, useState, type CSSProperties, type RefObject } from 'react'

type Options = {
  open: boolean
  anchorRef: RefObject<HTMLElement | null>
  popoverWidth: number
  popoverHeight: number
  gap?: number
}

export function useAnchoredPopover({
  open,
  anchorRef,
  popoverWidth,
  popoverHeight,
  gap = 8,
}: Options): CSSProperties {
  const [style, setStyle] = useState<CSSProperties>({ visibility: 'hidden' })

  useEffect(() => {
    if (!open) return

    function update() {
      const el = anchorRef.current
      if (!el) return

      const rect = el.getBoundingClientRect()
      const spaceBelow = window.innerHeight - rect.bottom - gap
      const spaceAbove = rect.top - gap
      const openUp = spaceBelow < popoverHeight && spaceAbove > spaceBelow

      let top = openUp ? rect.top - gap : rect.bottom + gap
      if (openUp) top -= popoverHeight

      let left = rect.left
      const maxLeft = window.innerWidth - popoverWidth - 16
      left = Math.max(16, Math.min(left, maxLeft))

      top = Math.max(16, Math.min(top, window.innerHeight - popoverHeight - 16))

      setStyle({
        position: 'fixed',
        top,
        left,
        width: popoverWidth,
        zIndex: 250,
        visibility: 'visible',
      })
    }

    update()
    window.addEventListener('resize', update)
    window.addEventListener('scroll', update, true)
    return () => {
      window.removeEventListener('resize', update)
      window.removeEventListener('scroll', update, true)
    }
  }, [open, anchorRef, popoverWidth, popoverHeight, gap])

  return open ? style : { visibility: 'hidden' as const }
}
